import unittest
from  unittest import mock

import os
import sys
import importlib.util
import types
import time
import io
from pathlib import Path


def _load_web_module():
    here = Path(__file__).resolve()
    web_engine_path = (here.parent.parent / "source" / "Web.py").resolve()
    if not web_engine_path.exists():
        raise FileNotFoundError(f"Web.py not found at: {web_engine_path}")

    _install_import_stubs()

    module_name = "micros_web_engine_under_test"
    spec = importlib.util.spec_from_file_location(module_name, str(web_engine_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {web_engine_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_buffer_module():
    here = Path(__file__).resolve()
    buffer_path = (here.parent.parent / "source" / "Buffer.py").resolve()
    if not buffer_path.exists():
        raise FileNotFoundError(f"Buffer.py not found at: {buffer_path}")

    _install_import_stubs()

    module_name = "micros_buffer_dependency"
    spec = importlib.util.spec_from_file_location(module_name, str(buffer_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {buffer_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _install_import_stubs():
    """Install minimal stub modules so Scheduler.py imports succeed unchanged."""
    m = types.ModuleType("uos")
    m.stat = os.stat
    sys.modules["uos"] = m

    m = types.ModuleType("Tasks")
    m.lm_exec = lambda *_a, **_k: True, ""
    m.lm_is_loaded = lambda *_a, **_k: True
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

    def setUp(self):
        self.engine = self.web_module.WebEngine("1.0.0")
        self.rx = self.buffer_module.SlidingBuffer(bytearray(1024))
        self.tx = self.buffer_module.SlidingBuffer(bytearray(1024))


    def test_status_parsing_valid(self):
        request = b"GET /index.html HTTP/1.1\r\nContent-Length:10"

        for i in range(len(request)):
            self.rx.write(request[i:i+1])
            self.engine.state(self.rx, self.tx)

        self.assertEqual(self.engine.method, b"GET")
        self.assertEqual(self.engine.url, b"index.html")
        self.assertEqual(self.engine.version, b"HTTP/1.1")
        self.assertEqual(self.rx.peek(), b"Content-Length:10")
        self.assertEqual(self.engine.state, self.engine._parse_headers_st)


    def test_status_parsing_incomplete_line(self):
        request = b"GET /index.html HTTP/1.1"

        for i in range(len(request)):
            self.rx.write(request[i:i+1])
            self.engine.state(self.rx, self.tx)
            if self.engine.state is None:
                break

        self.assertEqual(self.engine.method, None)
        self.assertEqual(self.engine.url, None)
        self.assertEqual(self.engine.version, None)
        self.assertEqual(self.engine.state, self.engine._parse_request_line_st)


    def test_status_parsing_unsupported_method(self):
        request = b"TRACE /index.html HTTP/1.1\r\n"

        for i in range(len(request)):
            self.rx.write(request[i:i+1])
            self.engine.state(self.rx, self.tx)
            if self.engine.state is None:
                break

        self.assertEqual(self.engine.method, b"TRACE")
        self.assertEqual(self.engine.url, b"index.html")
        self.assertEqual(self.engine.version, b"HTTP/1.1")
        self.assertEqual(self.engine.state, None)
        self.assertEqual(self.engine.status_code, 400)


    def test_status_parsing_unsupported_version(self):
        request = b"GET /index.html HTTP/2\r\n"

        for i in range(len(request)):
            self.rx.write(request[i:i+1])
            self.engine.state(self.rx, self.tx)
            if self.engine.state is None:
                break

        self.assertEqual(self.engine.method, b"GET")
        self.assertEqual(self.engine.url, b"index.html")
        self.assertEqual(self.engine.version, b"HTTP/2")
        self.assertEqual(self.engine.state, None)
        self.assertEqual(self.engine.status_code, 505)


    def test_header_parsing_valid(self):
        self.engine.state = self.engine._parse_headers_st
        request = b"Content-Length:10\r\nContent-Type:application/json\r\n\r\n"

        for i in range(len(request)):
            self.rx.write(request[i:i+1])
            self.engine.state(self.rx, self.tx)

        self.assertDictEqual({"content-length": 10, "content-type": "application/json"}, self.engine.headers)
        self.assertEqual(self.rx.peek(), b"")
        self.assertEqual(self.engine.state, self.engine._route_request_st)


    def test_header_parsing_incomplete_header(self):
        request = b"GET /index.html HTTP/1.1\r\nContent-Type\r\n\r\n"

        for i in range(len(request)):
            self.rx.write(request[i:i+1])
            self.engine.state(self.rx, self.tx)
            if self.engine.state is None:
                break

        self.assertEqual(self.engine.status_code, 400)
        self.assertEqual(self.engine.state, None)


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
        self.engine.state = self.engine._start_multipart_parser_st
        self.engine.headers["content-length"] = 100
        self.engine.mp_boundary = b"test-boundary"
        body_part = b"--test-boundary\r\nContent-Type:text/plain"

        for i in range(len(body_part)):
            self.rx.write(body_part[i:i+1])
            self.engine.state(self.rx, self.tx)

        self.assertEqual(self.engine.state, self.engine._parse_boundary_st)
        self.assertEqual(self.rx.peek(), b"Content-Type:text/plain")


    def test_multipart_receiver_boundary_mismatch(self):
        self.engine.state = self.engine._start_multipart_parser_st
        self.engine.headers["content-length"] = 100
        self.engine.mp_boundary = b"test-boundary"
        body_part = b"--test-boundary-delimiter\r\nContent-Type:text/plain"

        for i in range(len(body_part)):
            self.rx.write(body_part[i:i+1])
            self.engine.state(self.rx, self.tx)
            if self.engine.state is None:
                break

        self.assertEqual(self.engine.state, None)
        self.assertEqual(self.engine.status_code, 400)
        self.assertEqual(self.rx.peek(), b"--test-boundary-delimiter\r\n")


    def test_multipart_receiver_complete_part(self):
        self.engine.state = self.engine._parse_boundary_st
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
            self.assertEqual(self.engine.state, self.engine._parse_boundary_st)
            self.rx.write(body_part[i:i+1])
            self.engine.state(self.rx, self.tx)

        self.assertEqual(self.engine.state, self.engine._parse_complete_part_st)
        self.assertEqual(self.rx.peek(), body_part)

        self.engine.state(self.rx, self.tx)

        self.assertEqual(self.engine.state, self.engine._parse_boundary_st)
        test_callback.assert_called_once_with(
            {"content-disposition":"form-data;name=\"file-chunk\";filename=\"upload.txt\"Content-Type:text/plain"},
            b"Upload content", first=True, last=False
        )


    def test_multipart_receiver_last_part(self):
        self.engine.state = self.engine._parse_boundary_st
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
            self.assertEqual(self.engine.state, self.engine._parse_boundary_st)
            self.rx.write(body_part[i:i+1])
            self.engine.state(self.rx, self.tx)

        self.assertEqual(self.engine.state, self.engine._parse_complete_part_st)
        self.assertEqual(self.rx.peek(), body_part)

        self.engine.state(self.rx, self.tx)

        self.assertEqual(self.engine.state, None)
        self.assertEqual(self.engine.status_code, 200)
        test_callback.assert_called_once_with(
            {"content-disposition":"form-data;name=\"file-chunk\";filename=\"upload.txt\"Content-Type:text/plain"},
            b"Upload content", first=True, last=True
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
