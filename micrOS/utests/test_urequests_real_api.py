"""
Public-API tests for source/urequests.py.

These stay offline and sandbox-safe while still exercising the exported
request helpers (`get`) through fake socket transports.
"""

import importlib.util
import json
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
        import asyncio
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
    module_name = "micros_urequests_under_test_public"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, str(urequests_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {urequests_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


class _FakeSocket:
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.sent = []
        self.closed = False

    def settimeout(self, _value):
        return None

    def connect(self, _addr):
        return None

    def send(self, data):
        self.sent.append(data)
        return len(data)

    def write(self, data):
        self.sent.append(data)
        return len(data)

    def recv(self, _size):
        return self.chunks.pop(0) if self.chunks else b""

    def read(self, _size):
        return self.recv(_size)

    def close(self):
        self.closed = True


class TestURequestsRealApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.urequests = _load_urequests_module()

    def _run_get(self, chunks, url, jsonify=False):
        fake_socket = _FakeSocket(chunks)
        original_socket = self.urequests.socket
        original_host_to_addr = self.urequests._host_to_addr
        try:
            self.urequests.socket = lambda: fake_socket
            self.urequests._host_to_addr = lambda *_a, **_k: ("127.0.0.1", 80)
            status, body = self.urequests.get(url, jsonify=jsonify)
        finally:
            self.urequests.socket = original_socket
            self.urequests._host_to_addr = original_host_to_addr
        self.assertTrue(fake_socket.closed)
        return status, body, fake_socket

    def test_http_get_json(self):
        body = json.dumps({"lat": 47.4979, "lon": 19.0402, "timezone": "Europe/Budapest", "offset": 3600}).encode()
        status, parsed, fake_socket = self._run_get(
            [b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body],
            "http://example.com/json",
            jsonify=True,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(parsed, dict)
        self.assertIn("lat", parsed)
        self.assertIn("lon", parsed)
        self.assertIn("timezone", parsed)
        self.assertIn("offset", parsed)
        self.assertIn(b"GET /json HTTP/1.1\r\n", fake_socket.sent[0])

    def test_http_get_raw_body_is_json_text(self):
        body = b'{"lat": 47.4979, "lon": 19.0402}'
        status, raw, _ = self._run_get(
            [b"HTTP/1.1 200 OK\r\nContent-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body],
            "http://example.com/json",
            jsonify=False,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(raw, str)
        parsed = json.loads(raw)
        self.assertIn("lat", parsed)
        self.assertIn("lon", parsed)

    def test_http_get_chunked_raw_body(self):
        status, raw, _ = self._run_get(
            [
                b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n",
                b"5\r\nhello\r\n",
                b"6\r\n world\r\n0\r\n\r\n",
            ],
            "http://example.com/chunked",
            jsonify=False,
        )
        self.assertEqual(status, 200)
        self.assertEqual(raw, b"hello world")

    def test_http_get_chunked_json_body(self):
        status, parsed, _ = self._run_get(
            [
                b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n",
                b"c\r\n{\"ok\": true,",
                b"\r\n",
                b"8\r\n \"n\": 1}\r\n0\r\n\r\n",
            ],
            "http://example.com/chunked-json",
            jsonify=True,
        )
        self.assertEqual(status, 200)
        self.assertEqual(parsed, {"ok": True, "n": 1})


if __name__ == "__main__":
    unittest.main(verbosity=2)
