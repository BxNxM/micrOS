import unittest
from  unittest import mock

import os
import sys
import importlib.util
import types
import time
import io
from pathlib import Path


def setUpModule():
    print(f"== RUN {Path(__file__).name} ==")


def _load_web_module():
    here = Path(__file__).resolve()
    web_engine_path = (here.parent.parent / "source" / "Web.py").resolve()
    if not web_engine_path.exists():
        raise FileNotFoundError(f"Web.py not found at: {web_engine_path}")

    _install_import_stubs()
    _load_buffer_module()

    module_name = "micros_web_engine_under_test"
    spec = importlib.util.spec_from_file_location(module_name, str(web_engine_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {web_engine_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_buffer_module():
    if "Buffer" in sys.modules:
        return sys.modules["Buffer"]

    here = Path(__file__).resolve()
    buffer_path = (here.parent.parent / "source" / "Buffer.py").resolve()
    if not buffer_path.exists():
        raise FileNotFoundError(f"Buffer.py not found at: {buffer_path}")

    _install_import_stubs()

    module_name = "Buffer"
    spec = importlib.util.spec_from_file_location(module_name, str(buffer_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {buffer_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _install_import_stubs():
    """Install minimal stub modules required by Web.py/Buffer.py in CPython tests."""
    m = types.ModuleType("uos")
    m.stat = os.stat
    sys.modules["uos"] = m

    m = types.ModuleType("Tasks")
    m.lm_exec = lambda *_a, **_k: True, ""
    m.lm_is_loaded = lambda *_a, **_k: True
    class TaskBaseStub:
        @staticmethod
        async def feed(sleep_ms=1):
            import asyncio
            if hasattr(asyncio, "sleep_ms"):
                return await asyncio.sleep_ms(sleep_ms)
            return await asyncio.sleep(max(0, sleep_ms) / 1000)
    m.TaskBase = TaskBaseStub
    sys.modules["Tasks"] = m

    m = types.ModuleType("Files")
    class OSPathStub:
        WEB = "/web"
        pass
    m.OSPath = OSPathStub
    m.path_join = lambda *_a: os.path.join(*_a)
    sys.modules["Files"] = m

    m = types.ModuleType("Config")
    m.cfgget = lambda _k: ""
    sys.modules["Config"] = m

    m = types.ModuleType("Auth")
    m.PWD_KEY = "pwd"
    class AuthRequired(Exception):
        pass
    def sudo(func):
        def wrapper(*args, **kwargs):
            password = kwargs.get("pwd")
            if password != "secret":
                raise AuthRequired("Access denied")
            kwargs.pop("pwd", None)
            return func(*args, **kwargs)
        return wrapper
    m.AuthRequired = AuthRequired
    m.sudo = sudo
    sys.modules["Auth"] = m

    m = types.ModuleType("Debug")
    m.console_write = lambda *_a, **_k: None
    m.syslog = lambda *_a, **_k: None
    sys.modules["Debug"] = m

    m = types.ModuleType("simgc")
    m.mem_free = lambda: 1_000_000
    sys.modules["simgc"] = m


class _DummyWriter:
    def write(self, _data):
        return None

    async def drain(self):
        return None


class _WebEngineTestAdapter:
    """Mixin to provide minimal Client I/O surface for direct WebEngine instantiation in tests."""
    @property
    def writer(self):
        return _DummyWriter()

    async def read(self, decoding='utf8', timeout_seconds=0, read_bytes=None):
        return False, b""


class MockOpen:
    #builtin_open = open

    def open(self, *args, **kwargs):
        if args[0] == "/web/index.html":
            return io.BytesIO(b"<html><header>Test page</header><body>Test</body></html>")
        #return self.builtin_open(*args, **kwargs)


def fake_stat(size=1024):
    return os.stat_result((
        0o100644,        # st_mode (regular file, 644 perms)
        12345678,        # st_ino
        2049,            # st_dev
        1,               # st_nlink
        1000,            # st_uid
        1000,            # st_gid
        size,            # st_size
        int(time.time()),# st_atime
        int(time.time()),# st_mtime
        int(time.time()),# st_ctime
    ))


class TestWebStateMachine(unittest.TestCase):
    """
    Tests for the core functionality of the state machine.
    """

    @classmethod
    def setUpClass(cls):
        cls.web_module = _load_web_module()
        cls.buffer_module = _load_buffer_module()
        cls.WebEngineForTest = type(
            "WebEngineForTest",
            (_WebEngineTestAdapter, cls.web_module.WebEngine),
            {}
        )

    def setUp(self):
        self.web_module.WebEngine.ENDPOINTS.clear()
        self.engine = self.WebEngineForTest("1.0.0")
        self.rx = self.buffer_module.SlidingBuffer(bytearray(1024))
        self.tx = self.buffer_module.SlidingBuffer(bytearray(1024))


    def test_status_parsing_valid(self):
        request = b"GET /index.html HTTP/1.1\r\nContent-Length:10"

        for i in range(len(request)):
            self.rx.write(request[i:i+1])
            self.engine.engine_state(self.rx, self.tx)

        self.assertEqual(self.engine.method, b"GET")
        self.assertEqual(self.engine.url, b"index.html")
        self.assertEqual(self.engine.version, b"HTTP/1.1")
        self.assertEqual(self.rx.peek(), b"Content-Length:10")
        self.assertEqual(self.engine.engine_state, self.engine._parse_headers_st)


    def test_status_parsing_incomplete_line(self):
        request = b"GET /index.html HTTP/1.1"

        for i in range(len(request)):
            self.rx.write(request[i:i+1])
            self.engine.engine_state(self.rx, self.tx)
            if self.engine.engine_state is None:
                break

        self.assertEqual(self.engine.method, None)
        self.assertEqual(self.engine.url, None)
        self.assertEqual(self.engine.version, None)
        self.assertEqual(self.engine.engine_state, self.engine._parse_request_line_st)


    def test_status_parsing_unsupported_method(self):
        request = b"TRACE /index.html HTTP/1.1\r\n"

        for i in range(len(request)):
            self.rx.write(request[i:i+1])
            self.engine.engine_state(self.rx, self.tx)
            if self.engine.engine_state is None:
                break

        self.assertEqual(self.engine.method, b"TRACE")
        self.assertEqual(self.engine.url, b"index.html")
        self.assertEqual(self.engine.version, b"HTTP/1.1")
        self.assertEqual(self.engine.engine_state, None)
        self.assertEqual(self.engine.status_code, 405)


    def test_status_parsing_unsupported_version(self):
        request = b"GET /index.html HTTP/2\r\n"

        for i in range(len(request)):
            self.rx.write(request[i:i+1])
            self.engine.engine_state(self.rx, self.tx)
            if self.engine.engine_state is None:
                break

        self.assertEqual(self.engine.method, b"GET")
        self.assertEqual(self.engine.url, b"index.html")
        self.assertEqual(self.engine.version, b"HTTP/2")
        self.assertEqual(self.engine.engine_state, None)
        self.assertEqual(self.engine.status_code, 505)


    def test_header_parsing_valid(self):
        self.engine.engine_state = self.engine._parse_headers_st
        request = b"Content-Length:10\r\nContent-Type:application/json\r\n\r\n"

        for i in range(len(request)):
            self.rx.write(request[i:i+1])
            self.engine.engine_state(self.rx, self.tx)

        self.assertDictEqual({"content-length": 10, "content-type": "application/json"}, self.engine.headers)
        self.assertEqual(self.rx.peek(), b"")
        self.assertEqual(self.engine.engine_state, self.engine._route_request_st)


    def test_header_parsing_incomplete_header(self):
        request = b"GET /index.html HTTP/1.1\r\nContent-Type\r\n\r\n"

        for i in range(len(request)):
            self.rx.write(request[i:i+1])
            self.engine.engine_state(self.rx, self.tx)
            if self.engine.engine_state is None:
                break

        self.assertEqual(self.engine.status_code, 400)
        self.assertEqual(self.engine.engine_state, None)


    def test_multipart_parser(self):
        for case in [
            ({"content-type": "multipart/form-data; boundary =\"test-boundary\""}, "test-boundary"),
            ({"content-type": "multipart/form-data ;boundary= test-boundary "}, "test-boundary"),
            ({"content-type": "multipart/form-data;boundary=a test boundary "}, "a test boundary")
        ]:
            with self.subTest(headers=case[0], expected = case[1]):
                self.assertEqual(self.engine._is_multipart(case[0]), case[1])

        for case in [
            {},
            {"content-type": "multipart/form-data"},
            {"content-type": "multipart/form-data;boundary=\"\""},
            {"content-type": "multipart/form-data;boundary=\r\n"}
        ]:
            with self.subTest(headers=case, expected = None):
                self.assertEqual(self.engine._is_multipart(case), None)


    def test_multipart_receiver_valid(self):
        self.engine.engine_state = self.engine._start_multipart_parser_st
        self.engine.headers["content-length"] = 100
        self.engine.mp_boundary = b"test-boundary"
        body_part = b"--test-boundary\r\nContent-Type:text/plain"

        for i in range(len(body_part)):
            self.rx.write(body_part[i:i+1])
            self.engine.engine_state(self.rx, self.tx)

        self.assertEqual(self.engine.engine_state, self.engine._parse_boundary_st)
        self.assertEqual(self.rx.peek(), b"Content-Type:text/plain")


    def test_multipart_receiver_boundary_mismatch(self):
        self.engine.engine_state = self.engine._start_multipart_parser_st
        self.engine.headers["content-length"] = 100
        self.engine.mp_boundary = b"test-boundary"
        body_part = b"--test-boundary-delimiter\r\nContent-Type:text/plain"

        for i in range(len(body_part)):
            self.rx.write(body_part[i:i+1])
            self.engine.engine_state(self.rx, self.tx)
            if self.engine.engine_state is None:
                break

        self.assertEqual(self.engine.engine_state, None)
        self.assertEqual(self.engine.status_code, 400)
        self.assertEqual(self.rx.peek(), b"--test-boundary-delimiter\r\n")


    def test_multipart_receiver_complete_part(self):
        self.engine.engine_state = self.engine._parse_boundary_st
        self.engine.url = b"/api/test"
        self.engine.method = b"GET"

        test_callback = mock.Mock()
        self.engine.register("/api/test", test_callback)

        self.engine.headers["content-length"] = 1000
        self.engine.mp_boundary = b"test-boundary"
        self.engine.mp_delimiter = b'--test-boundary\r\n'
        self.engine.mp_closing_delimiter = b'--test-boundary--'

        body_part = (
            b"Content-Disposition:form-data;"
            b"name=\"file-chunk\";filename=\"upload.txt\"Content-Type:text/plain\r\n\r\n"
            b"Upload content\r\n"
            b"--test-boundary\r\n"
        )

        for i in range(len(body_part)):
            self.assertEqual(self.engine.engine_state, self.engine._parse_boundary_st)
            self.rx.write(body_part[i:i+1])
            self.engine.engine_state(self.rx, self.tx)

        self.assertEqual(self.engine.engine_state, self.engine._parse_complete_part_st)
        self.assertEqual(self.rx.peek(), body_part)

        self.engine.engine_state(self.rx, self.tx)

        self.assertEqual(self.engine.engine_state, self.engine._parse_boundary_st)
        test_callback.assert_called_once_with(
            {"content-disposition":"form-data;name=\"file-chunk\";filename=\"upload.txt\"Content-Type:text/plain"},
            b"Upload content", first=True, last=False
        )


    def test_multipart_receiver_last_part(self):
        self.engine.engine_state = self.engine._parse_boundary_st
        self.engine.url = b"/api/test"
        self.engine.method = b"GET"
        self.engine.headers["content-length"] = 129
        self.engine.mp_boundary = b"test-boundary"
        self.engine.mp_delimiter = b'--test-boundary\r\n'
        self.engine.mp_closing_delimiter = b'--test-boundary--'

        test_callback = mock.Mock(return_value=("text/plain", "OK"))
        self.engine.register("/api/test", test_callback)

        body_part = (
            b"Content-Disposition:form-data;"
            b"name=\"file-chunk\";filename=\"upload.txt\"Content-Type:text/plain\r\n\r\n"
            b"Upload content\r\n"
            b"--test-boundary--"
        )

        for i in range(len(body_part)):
            self.assertEqual(self.engine.engine_state, self.engine._parse_boundary_st)
            self.rx.write(body_part[i:i+1])
            self.engine.engine_state(self.rx, self.tx)

        self.assertEqual(self.engine.engine_state, self.engine._parse_complete_part_st)
        self.assertEqual(self.rx.peek(), body_part)

        self.engine.engine_state(self.rx, self.tx)

        self.assertEqual(self.engine.engine_state, None)
        self.assertEqual(self.engine.status_code, 200)
        test_callback.assert_called_once_with(
            {"content-disposition":"form-data;name=\"file-chunk\";filename=\"upload.txt\"Content-Type:text/plain"},
            b"Upload content", first=True, last=True
        )

    def test_parse_rest_cmd_preserves_quoted_values(self):
        self.assertEqual(
            self.web_module._parse_rest_cmd('system/clock/"my value"/foo-bar'),
            ['system', 'clock', '"my value"', 'foo', 'bar']
        )

    def test_html_endpoint_does_not_auto_load_auth_script(self):
        callback = mock.Mock(return_value=("text/html", "<html><head></head><body>OK</body></html>"))
        self.engine.register("api/page", callback)
        self.engine.url = b"api/page"
        self.engine.method = b"GET"
        self.engine.headers = {}

        self.engine._lm_endpoint_st(self.rx, self.tx)

        response = bytes(self.tx.peek())
        self.assertEqual(self.engine.status_code, 200)
        self.assertNotIn(b'<script src="/auth.js"></script>', response)
        callback.assert_called_once_with(self.engine.headers, b"")

    def test_static_html_streams_without_rewrite(self):
        body = b"<html><head><title>Test</title></head><body>OK</body></html>"

        def fake_open(path, mode="r", *_args, **_kwargs):
            self.assertEqual(path, "/web/index.html")
            self.assertEqual(mode, "rb")
            return io.BytesIO(body)

        with mock.patch.object(self.web_module, "stat", return_value=fake_stat(len(body))), \
             mock.patch("builtins.open", fake_open):
            response_handler = self.engine._send_file_st(self.rx, self.tx, "index.html")

        response_head = bytes(self.tx.peek())
        self.assertIsInstance(response_handler, io.BytesIO)
        self.assertEqual(self.engine.status_code, 200)
        self.assertEqual(self.engine.response_headers[b"content-length"], str(len(body)).encode())
        self.assertNotIn(b'<script src="/auth.js"></script>', response_head)
        self.assertEqual(response_handler.getvalue(), body)

    def test_mounted_html_streams_without_rewrite(self):
        body = b"<html><head></head><body>User data</body></html>"
        self.web_module.WebEngine.WEB_MOUNTS["$data"] = "/data"

        def fake_open(path, mode="r", *_args, **_kwargs):
            self.assertEqual(path, "/data/page.html")
            self.assertEqual(mode, "rb")
            return io.BytesIO(body)

        try:
            with mock.patch.object(self.web_module, "stat", return_value=fake_stat(len(body))), \
                 mock.patch("builtins.open", fake_open):
                response_handler = self.engine._send_file_st(self.rx, self.tx, "$data/page.html")
        finally:
            self.web_module.WebEngine.WEB_MOUNTS.pop("$data", None)

        self.assertIsInstance(response_handler, io.BytesIO)
        self.assertEqual(self.engine.status_code, 200)
        self.assertEqual(self.engine.response_headers[b"content-length"], str(len(body)).encode())
        self.assertEqual(response_handler.getvalue(), body)

    def test_sudo_endpoint_rejects_missing_header_at_execution(self):
        callback = mock.Mock(return_value=("application/json", {"ok": True}))
        wrapped = sys.modules["Auth"].sudo(callback)
        self.engine.register("api/test", wrapped)
        self.assertIs(self.engine.ENDPOINTS[b"api/test"][b"GET"], wrapped)
        self.engine.url = b"api/test"
        self.engine.method = b"GET"
        self.engine.headers = {"accept": "*/*"}

        self.engine._lm_endpoint_st(self.rx, self.tx)

        self.assertEqual(self.engine.status_code, 401)
        self.assertEqual(self.engine.response_headers[b"content-type"], b"application/json")
        self.assertNotIn(b"www-authenticate", bytes(self.tx.peek()).lower())
        callback.assert_not_called()

    def test_sudo_endpoint_accepts_get_header_at_execution(self):
        callback = mock.Mock(return_value=("application/json", {"ok": True}))
        wrapped = sys.modules["Auth"].sudo(callback)
        self.engine.register("api/test", wrapped)
        self.engine.url = b"api/test"
        self.engine.method = b"GET"
        self.engine.headers = {"x-micros-auth": "secret"}

        self.engine._lm_endpoint_st(self.rx, self.tx)

        self.assertEqual(self.engine.status_code, 200)
        callback.assert_called_once_with(self.engine.headers, b"")

    def test_plain_endpoint_ignores_auth_header_at_execution(self):
        callback = mock.Mock(return_value=("application/json", {"ok": True}))
        self.engine.register("api/test", callback)
        self.engine.url = b"api/test"
        self.engine.method = b"GET"
        self.engine.headers = {"x-micros-auth": "secret"}

        self.engine._lm_endpoint_st(self.rx, self.tx)

        self.assertEqual(self.engine.status_code, 200)
        callback.assert_called_once_with(self.engine.headers, b"")

    def test_sudo_endpoint_browser_get_returns_popup_shell(self):
        callback = mock.Mock(return_value=("text/plain", "ok"))
        self.engine.register("api/test", sys.modules["Auth"].sudo(callback))
        self.engine.url = b"api/test"
        self.engine.method = b"GET"
        self.engine.headers = {"accept": "text/html,application/xhtml+xml"}

        self.engine._lm_endpoint_st(self.rx, self.tx)

        body = bytes(self.tx.peek()).lower()
        self.assertEqual(self.engine.status_code, 401)
        self.assertEqual(self.engine.response_headers[b"content-type"], b"text/html")
        self.assertIn(b"/auth.js", body)
        self.assertIn(b"data-micros-auth", body)
        self.assertNotIn(b"www-authenticate", body)
        callback.assert_not_called()

    def test_sudo_endpoint_accepts_post_header_at_execution(self):
        callback = mock.Mock(return_value=("application/json", {"ok": True}))
        self.engine.register("api/test", sys.modules["Auth"].sudo(callback), "POST")
        self.engine.url = b"api/test"
        self.engine.method = b"POST"
        self.engine.headers = {
            "x-micros-auth": "secret",
            "content-length": 2
        }
        self.rx.write(b"{}")

        self.engine._lm_endpoint_st(self.rx, self.tx)

        self.assertEqual(self.engine.status_code, 200)
        callback.assert_called_once_with(self.engine.headers, b"{}")

    def test_sudo_endpoint_accepts_delete_header_at_execution(self):
        callback = mock.Mock(return_value=("application/json", {"ok": True}))
        self.engine.register("api/test", sys.modules["Auth"].sudo(callback), "DELETE")
        self.engine.url = b"api/test"
        self.engine.method = b"DELETE"
        self.engine.headers = {"x-micros-auth": "secret"}

        self.engine._lm_endpoint_st(self.rx, self.tx)

        self.assertEqual(self.engine.status_code, 200)
        callback.assert_called_once_with(self.engine.headers, b"")

    def test_sudo_multipart_accepts_header_at_execution(self):
        self.engine.engine_state = self.engine._parse_boundary_st
        self.engine.url = b"/api/test"
        self.engine.method = b"POST"
        self.engine.headers = {"content-length": 129, "x-micros-auth": "secret"}
        self.engine.mp_boundary = b"test-boundary"
        self.engine.mp_delimiter = b'--test-boundary\r\n'
        self.engine.mp_closing_delimiter = b'--test-boundary--'

        callback = mock.Mock(return_value=("application/json", {"ok": True}))
        self.engine.register("/api/test", sys.modules["Auth"].sudo(callback), "POST")

        body_part = (
            b"Content-Disposition:form-data;"
            b"name=\"file-chunk\";filename=\"upload.txt\"Content-Type:text/plain\r\n\r\n"
            b"Upload content\r\n"
            b"--test-boundary--"
        )

        for i in range(len(body_part)):
            self.assertEqual(self.engine.engine_state, self.engine._parse_boundary_st)
            self.rx.write(body_part[i:i+1])
            self.engine.engine_state(self.rx, self.tx)

        self.assertEqual(self.engine.engine_state, self.engine._parse_complete_part_st)
        self.engine.engine_state(self.rx, self.tx)

        self.assertEqual(self.engine.status_code, 200)
        callback.assert_called_once_with(
            {"content-disposition": "form-data;name=\"file-chunk\";filename=\"upload.txt\"Content-Type:text/plain"},
            b"Upload content", first=True, last=True
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
