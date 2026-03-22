import asyncio
import importlib.util
import socket
import ssl
import sys
import types
import unittest
from pathlib import Path


def setUpModule():
    print(f"== RUN {Path(__file__).name} ==")


def _install_import_stubs():
    m = types.ModuleType("usocket")
    m.socket = socket.socket
    m.getaddrinfo = socket.getaddrinfo
    sys.modules["usocket"] = m

    m = types.ModuleType("ussl")
    m.wrap_socket = getattr(ssl, "wrap_socket", lambda sock, *args, **kwargs: sock)
    sys.modules["ussl"] = m

    m = types.ModuleType("uasyncio")
    async def open_connection(*args, **kwargs):
        return await asyncio.open_connection(*args, **kwargs)
    m.open_connection = open_connection
    sys.modules["uasyncio"] = m

    m = types.ModuleType("Debug")
    m.syslog = lambda *_a, **_k: None
    sys.modules["Debug"] = m


def _load_urequests_module():
    here = Path(__file__).resolve()
    urequests_path = (here.parent.parent / "source" / "urequests.py").resolve()
    if not urequests_path.exists():
        raise FileNotFoundError(f"urequests.py not found at: {urequests_path}")

    _install_import_stubs()

    module_name = "micros_urequests_under_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, str(urequests_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {urequests_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


class _FakeSocket:
    def __init__(self, recv_chunks=None):
        self.recv_chunks = list(recv_chunks or [])
        self.sent = []
        self.timeout = None
        self.connected = None
        self.closed = False

    def settimeout(self, value):
        self.timeout = value

    def connect(self, addr):
        self.connected = addr

    def send(self, data):
        self.sent.append(data)
        return len(data)

    def write(self, data):
        self.sent.append(data)
        return len(data)

    def recv(self, _size):
        return self.recv_chunks.pop(0) if self.recv_chunks else b""

    def read(self, _size):
        return self.recv(_size)

    def close(self):
        self.closed = True


class _FakeReader:
    def __init__(self, chunks):
        self.chunks = list(chunks)

    async def read(self, _size):
        return self.chunks.pop(0) if self.chunks else b""


class _FakeWriter:
    def __init__(self):
        self.data = []
        self.closed = False
        self.wait_closed_called = False

    def write(self, data):
        self.data.append(data)

    async def drain(self):
        return None

    def close(self):
        self.closed = True

    async def wait_closed(self):
        self.wait_closed_called = True


class TestURequests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.urequests = _load_urequests_module()

    def test_build_request_returns_bytes_and_body_once(self):
        req = self.urequests._build_request(
            "example.com", "POST", "api", {}, json={"a": 1}
        )
        self.assertIsInstance(req, (bytes, bytearray))
        self.assertIn(b"POST /api HTTP/1.1\r\n", req)
        self.assertIn(b"Content-Type: application/json\r\n", req)
        self.assertTrue(req.endswith(b'{"a": 1}'))

    def test_read_response_with_content_length(self):
        chunks = [
            b"HTTP/1.1 200 OK\r\nContent-Length: 11\r\n\r\nhello",
            b" world",
        ]
        status, body = self.urequests._read_response(lambda _n: chunks.pop(0) if chunks else b"", 16)
        self.assertEqual(status, 200)
        self.assertEqual(body, "hello world")

    def test_read_response_with_chunked_body(self):
        chunks = [
            b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n",
            b"5\r\nhello\r\n",
            b"6\r\n world\r\n0\r\n\r\n",
        ]
        status, body = self.urequests._read_response(lambda _n: chunks.pop(0) if chunks else b"", 16)
        self.assertEqual(status, 200)
        self.assertEqual(body, b"hello world")

    def test_request_closes_socket_on_parse_failure(self):
        fake_socket = _FakeSocket([b"HTTP/1.1 200 OK\r\n", b""])
        original_socket = self.urequests.socket
        original_host_to_addr = self.urequests._host_to_addr
        try:
            self.urequests.socket = lambda: fake_socket
            self.urequests._host_to_addr = lambda *_a, **_k: ("127.0.0.1", 80)
            with self.assertRaises(ValueError):
                self.urequests.request("GET", "http://example.com/test")
        finally:
            self.urequests.socket = original_socket
            self.urequests._host_to_addr = original_host_to_addr
        self.assertTrue(fake_socket.closed)

    def test_https_request_uses_server_hostname_when_supported(self):
        fake_socket = _FakeSocket([b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"])
        wrapped = _FakeSocket([b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"])
        captured = {}
        original_socket = self.urequests.socket
        original_host_to_addr = self.urequests._host_to_addr
        original_wrap_socket = self.urequests.wrap_socket
        try:
            self.urequests.socket = lambda: fake_socket
            self.urequests._host_to_addr = lambda *_a, **_k: ("127.0.0.1", 443)
            def _wrap_socket(sock, server_hostname=None):
                captured["sock"] = sock
                captured["server_hostname"] = server_hostname
                return wrapped
            self.urequests.wrap_socket = _wrap_socket
            status, body = self.urequests.request("GET", "https://example.com/test")
        finally:
            self.urequests.socket = original_socket
            self.urequests._host_to_addr = original_host_to_addr
            self.urequests.wrap_socket = original_wrap_socket
        self.assertEqual(status, 200)
        self.assertEqual(body, "ok")
        self.assertIs(captured["sock"], fake_socket)
        self.assertEqual(captured["server_hostname"], "example.com")
        self.assertTrue(wrapped.closed)

    def test_https_request_falls_back_when_wrap_socket_has_no_server_hostname_kwarg(self):
        fake_socket = _FakeSocket([b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"])
        wrapped = _FakeSocket([b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"])
        original_socket = self.urequests.socket
        original_host_to_addr = self.urequests._host_to_addr
        original_wrap_socket = self.urequests.wrap_socket
        try:
            self.urequests.socket = lambda: fake_socket
            self.urequests._host_to_addr = lambda *_a, **_k: ("127.0.0.1", 443)
            def _wrap_socket(sock, **kwargs):
                if "server_hostname" in kwargs:
                    raise TypeError("unsupported kwarg")
                return wrapped
            self.urequests.wrap_socket = _wrap_socket
            status, body = self.urequests.request("GET", "https://example.com/test")
        finally:
            self.urequests.socket = original_socket
            self.urequests._host_to_addr = original_host_to_addr
            self.urequests.wrap_socket = original_wrap_socket
        self.assertEqual(status, 200)
        self.assertEqual(body, "ok")
        self.assertTrue(wrapped.closed)

    def test_arequest_uses_same_parser_and_closes_writer(self):
        reader = _FakeReader([
            b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n",
            b"ok",
        ])
        writer = _FakeWriter()
        original_open = self.urequests.asyncio.open_connection
        original_host_to_addr = self.urequests._host_to_addr
        try:
            async def _open_connection(*_a, **_k):
                return reader, writer
            self.urequests.asyncio.open_connection = _open_connection
            self.urequests._host_to_addr = lambda *_a, **_k: ("127.0.0.1", 80)
            status, body = asyncio.run(self.urequests.arequest("GET", "http://example.com/test"))
        finally:
            self.urequests.asyncio.open_connection = original_open
            self.urequests._host_to_addr = original_host_to_addr
        self.assertEqual(status, 200)
        self.assertEqual(body, "ok")
        self.assertTrue(writer.closed)
        self.assertTrue(writer.wait_closed_called)

    def test_arequest_handles_chunked_body(self):
        reader = _FakeReader([
            b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n",
            b"5\r\nhello\r\n",
            b"6\r\n world\r\n0\r\n\r\n",
        ])
        writer = _FakeWriter()
        original_open = self.urequests.asyncio.open_connection
        original_host_to_addr = self.urequests._host_to_addr
        try:
            async def _open_connection(*_a, **_k):
                return reader, writer
            self.urequests.asyncio.open_connection = _open_connection
            self.urequests._host_to_addr = lambda *_a, **_k: ("127.0.0.1", 80)
            status, body = asyncio.run(self.urequests.arequest("GET", "http://example.com/chunked"))
        finally:
            self.urequests.asyncio.open_connection = original_open
            self.urequests._host_to_addr = original_host_to_addr
        self.assertEqual(status, 200)
        self.assertEqual(body, b"hello world")
        self.assertTrue(writer.closed)
        self.assertTrue(writer.wait_closed_called)

    def test_arequest_handles_chunked_json_body(self):
        reader = _FakeReader([
            b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n",
            b"c\r\n{\"ok\": true,",
            b"\r\n",
            b"8\r\n \"n\": 1}\r\n0\r\n\r\n",
        ])
        writer = _FakeWriter()
        original_open = self.urequests.asyncio.open_connection
        original_host_to_addr = self.urequests._host_to_addr
        try:
            async def _open_connection(*_a, **_k):
                return reader, writer
            self.urequests.asyncio.open_connection = _open_connection
            self.urequests._host_to_addr = lambda *_a, **_k: ("127.0.0.1", 80)
            status, body = asyncio.run(self.urequests.arequest("GET", "http://example.com/chunked-json", jsonify=True))
        finally:
            self.urequests.asyncio.open_connection = original_open
            self.urequests._host_to_addr = original_host_to_addr
        self.assertEqual(status, 200)
        self.assertEqual(body, {"ok": True, "n": 1})
        self.assertTrue(writer.closed)
        self.assertTrue(writer.wait_closed_called)

    def test_arequest_connection_failure_returns_500(self):
        original_open = self.urequests.asyncio.open_connection
        original_host_to_addr = self.urequests._host_to_addr
        try:
            async def _open_connection(*_a, **_k):
                raise OSError("ECONNABORTED")
            self.urequests.asyncio.open_connection = _open_connection
            self.urequests._host_to_addr = lambda *_a, **_k: ("127.0.0.1", 80)
            status, body = asyncio.run(self.urequests.arequest("GET", "http://example.com/fail"))
        finally:
            self.urequests.asyncio.open_connection = original_open
            self.urequests._host_to_addr = original_host_to_addr
        self.assertEqual(status, 500)
        self.assertIn("ECONNABORTED", body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
