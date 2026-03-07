"""
Module is responsible for webserver state machine dedicated
to micrOS framework, with partial guarantees on RFC compliance.
Built-in-function:
- response
    - landing page: index.html
    - rest/                                     - call load modules, e.x.: system/top
    - file response (.html, .css, .js, .jpeg)   - generic file server feature
    - "virtual" endpoints                       - to reply from script on a defined endpoint
        - stream                                - data streaming (e.g. image/jpeg)

Designed by Marcell Ban aka BxNxM and szeka9 (GitHub)
"""

from re import compile as recompile
from json import dumps, loads
from io import BytesIO
from uos import stat
from Tasks import lm_exec, lm_is_loaded, TaskBase
from Config import cfgget
from Files import OSPath, path_join
from Buffer import SlidingBuffer, BufferFullError, MemoryPool
from Debug import console_write, syslog

try:
    from gc import mem_free
except:
    console_write("[SIMULATOR MODE GC IMPORT]")
    from simgc import mem_free


def url_path_resolve(path:str) -> tuple[bool, str]:
    """
    :param path: input path
    Return: isError, absolutePath
    """
    # $Extended mount check: WEB_MOUNTS (/modules and /web)
    path = path.lstrip("/")
    if path.startswith("$"):
        mount_alias = path.split("/")[0]
        mount_path = WebEngine.WEB_MOUNTS.get(mount_alias, None)
        if mount_path is None:
            return True, f"Invalid mount point: {mount_alias}"
        mount_path = path.replace(mount_alias, mount_path)
        return False, mount_path
    # Default web path: /web
    return False, path_join(OSPath.WEB, path)


class HeaderParsingError(ValueError):
    """Exception for errors occurring while parsing HTTP/MIME headers"""

#################################################################
#                   Pre-allocated Memory Buffer                 #
#################################################################

class Buffer:
    # Constants for memory footprint
    MEM_CAP  = 0.1              # Default memory cap (percentage / 100) of free heap
    SEND_BUF_MIN_BYTES = 512    # Minimum buffer size for responses
    SEND_BUF_MAX_BYTES = 4096   # Max buffer size for responses
    RECV_BUF_MIN_BYTES = 2048   # Minimum buffer size for requests
    RECV_BUF_MAX_BYTES = 4096   # Max buffer size for requests
    CONN_OVERHEAD = 1024        # Overhead per connection
    MTU_SIZE = 1460             # TCP maximum transmission unit
    # Timing settings
    STATE_MACHINE_SLEEP_MS = 2
    RESP_HANDLER_SLEEP_MS = 2
    RECV_TIMEOUT_SECONDS = 10
    # Static buffer pools - initialized by init_pools()
    RECV_POOL = None
    SEND_POOL = None
    __slots__ = (
        "engine_state",
        "__writer",
        "__reader",
        "_prev_state",
        "_recv_buf",
        "_send_buf"
    )

    def __init__(self, writer, reader):
        """
        :param writer: communication writer with: .write(...) and .drain() methods
        :param reader: communication reader method
        """
        self.engine_state = None
        self._prev_state = None
        self._recv_buf = None
        self._send_buf = None
        self.__writer = writer
        self.__reader = reader

    def on_failure(self, tx, info):
        raise NotImplementedError("Child class must implement on_failure method...!")

    def on_buffer_full(self, tx):
        raise NotImplementedError("Child class must implement on_buffer_full method...!")

    def on_timeout(self, tx):
        raise NotImplementedError("Child class must implement on_timeout method...!")

    @staticmethod
    def init_pools():
        """
        Initialize pool of buffers for sending/receiving based on different profiles
        """
        mem_available = mem_free()
        con_limit = min(
                        max(1, int(cfgget("aioqueue"))),
                        max(1, int(cfgget("webui_max_con")))
                    )
        usable = int(Buffer.MEM_CAP * mem_available)
        is_low_memory = (usable / con_limit) < \
            (Buffer.RECV_BUF_MAX_BYTES + Buffer.SEND_BUF_MAX_BYTES + Buffer.CONN_OVERHEAD)
        if is_low_memory:
            syslog((
                "[INFO] Webcli.init_pools: low-memory mode with reduced buffer size, "
                "decrease webui_max_con to use larger buffers"
            ))
        recv_size = Buffer.RECV_BUF_MIN_BYTES if is_low_memory else Buffer.RECV_BUF_MAX_BYTES
        send_size = Buffer.SEND_BUF_MIN_BYTES if is_low_memory else Buffer.SEND_BUF_MAX_BYTES
        per_conn = recv_size + send_size + Buffer.CONN_OVERHEAD
        if usable < per_conn:
            raise MemoryError((
                f"Insufficient memory for webserver: {mem_available // 1024} KB, "
                f"at least {per_conn // 1024} KB required"
            ))
        con_limit = min(
            usable // per_conn,
            con_limit
        )
        syslog((
            f"[INFO] Webcli.init_pools: {con_limit} connection(s) allowed"
        ))
        Buffer.RECV_POOL = MemoryPool(recv_size, con_limit, wrapper=SlidingBuffer)
        Buffer.SEND_POOL = MemoryPool(send_size, con_limit, wrapper=SlidingBuffer)


    async def _flush_response(self):
        data = self._send_buf.peek()
        for i in range(0, len(data), Buffer.MTU_SIZE):
            self.__writer.write(data[i:i + Buffer.MTU_SIZE])
            await self.__writer.drain()
        self._send_buf.consume()

    async def _reserve_buffers(self):
        if Buffer.SEND_POOL is None or Buffer.RECV_POOL is None:
            raise RuntimeError("Buffer pools are uninitialized")

        while not self._recv_buf or not self._send_buf:
            if not self._recv_buf:
                self._recv_buf = Buffer.RECV_POOL.reserve()
            if not self._send_buf:
                self._send_buf = Buffer.SEND_POOL.reserve()
            await TaskBase.feed(sleep_ms=Buffer.STATE_MACHINE_SLEEP_MS)

    async def _run_state_machine(self):
        if self._prev_state == self.engine_state or self._prev_state is None:
            num_read = await self._read_to_buf()
            if not num_read:
                return
        try:
            resp_handler = None
            while self.engine_state is not None:
                self._prev_state = self.engine_state
                resp_handler = self.engine_state(self._recv_buf, self._send_buf)
                if not self._send_buf.size():
                    break
                await self._flush_response()
                await TaskBase.feed(sleep_ms=Buffer.STATE_MACHINE_SLEEP_MS)
        except BufferFullError:
            self.on_failure(self._send_buf, b'Buffer full')
            await self._flush_response()
            return
        except Exception as e:
            syslog(f"[ERR] run_web: {e}")
            self.on_failure(self._send_buf, str(e).encode("ascii"))
            await self._flush_response()
            return
        if self.engine_state is None and resp_handler is not None:
            await self._response_handler(resp_handler)

    async def _read_to_buf(self):
        buf_free = self._recv_buf.capacity - self._recv_buf.size()
        if not buf_free:
            self.on_buffer_full(self._send_buf)
            await self._flush_response()
            return 0
        error, request = await self.__reader(decoding=None,
                                         timeout_seconds=Buffer.RECV_TIMEOUT_SECONDS,
                                         read_bytes=buf_free)
        if error:
            self.on_failure(self._send_buf, b"Read error")
            await self._flush_response()
            return 0
        if not request:
            self.on_timeout(self._send_buf)
            await self._flush_response()
            return 0
        self._recv_buf.write(request)
        return len(request)

    async def _response_handler(self, resp_handler):
        if "closure" == type(resp_handler).__name__:
            for is_finished in resp_handler(self._send_buf):
                await self._flush_response()
                if is_finished:
                    break
                await TaskBase.feed(sleep_ms=Buffer.RESP_HANDLER_SLEEP_MS)

        elif hasattr(resp_handler, "readinto"):
            with resp_handler as rh:
                while True:
                    view = self._send_buf.writable_view()
                    num_read = rh.readinto(view)
                    if not num_read:
                        break
                    self._send_buf.commit(num_read)
                    await self._flush_response()
                    await TaskBase.feed(sleep_ms=Buffer.RESP_HANDLER_SLEEP_MS)

        else:
            self.on_failure(self._send_buf, f"Invalid response handler {type(resp_handler).__name__}".encode("ascii"))
            await self._flush_response()


#################################################################
#                   WebEngine - HTTP/REST Server                #
#################################################################

class WebEngine(Buffer):
    """
    HTTP protocol parser state machine
    - provides an adapter/routing layer for micrOS load modules
    - supports multipart request and response handling
    - resolves static resources by returning a stream objects (FileIO)
    """
    __slots__ = [
        "status_code",
        "response_headers",
        "version",
        "headers",
        "method",
        "url",
        "content_length_cnt",
        "mp_first_part",
        "mp_boundary",
        "mp_delimiter",
        "mp_closing_delimiter"
    ]

    ENDPOINTS = {}
    AUTH = cfgget('auth')
    VERSION = "n/a"
    RESP_HEADERS = {
        200: b"HTTP/1.1 200 OK",
        400: b"HTTP/1.1 400 Bad Request",
        404: b"HTTP/1.1 404 Not Found",
        408: b"HTTP/1.1 408 Request Timeout",
        413: b"HTTP/1.1 413 Content Too Large",
        415: b"HTTP/1.1 415 Unsupported Media Type",
        500: b"HTTP/1.1 500 Internal Server Error",
        503: b"HTTP/1.1 503 Service Unavailable",
        505: b"HTTP/1.1 505 Version Not Supported"
    }
    CONTENT_TYPES = {
        b"html": b"text/html",
        b"css": b"text/css",
        b"js": b"application/javascript",
        b"json": b"application/json",
        b"ico": b"image/x-icon",
        b"jpeg": b"image/jpeg",
        b"jpg": b"image/jpeg",
        b"png": b"image/png",
        b"txt": b"text/plain",
        b"gif": b"image/gif"
    }
    GET = b"GET"
    POST = b"POST"
    DELETE = b"DELETE"
    METHODS = (GET, POST, DELETE)
    WEB_MOUNTS = {}

    def __init__(self, version):
        # Init Buffer methods and self.engine_state
        super().__init__(self.writer, self.read)
        # Init WebEngine ...
        WebEngine.VERSION = version
        # [State machine]
        self.engine_state = self._parse_request_line_st
        self.status_code = None
        self.response_headers = {}
        # [Received request]
        self.version = None
        self.headers = {}
        self.method = None
        self.url = None
        self.content_length_cnt = 0
        # [Received request] - multipart
        self.mp_first_part = True
        self.mp_boundary = None
        self.mp_delimiter = None
        self.mp_closing_delimiter = None

    # =========================================
    # Public methods for load modules
    # =========================================

    @staticmethod
    def register(endpoint:str, callback:object|str, method:str='GET') -> None:
        """
        PUBLIC METHOD FOR LMs: Webengine endpoint registration handler
        :param endpoint: name of the endpoint
        :param callback: callback function (WebEngine compatible: return:  html_type, content)
        :param method: HTTP method name
        """
        endpoint = endpoint.encode("ascii")
        method = method.encode("ascii")
        if not endpoint in WebEngine.ENDPOINTS:
            WebEngine.ENDPOINTS[endpoint] = {}
        if method not in WebEngine.METHODS:
            raise ValueError(f"method must be one of {WebEngine.METHODS}")
        WebEngine.ENDPOINTS[endpoint][method] = callback


    @staticmethod
    def web_mounts(modules:bool=None, data:bool=None, logs:bool=None) -> dict:
        """
        PUBLIC METHOD FOR LMs: WebEngine access path handler
        - default path: /web
        - extended path access: with $modules and $data dirs
        """
        def _update(state, alias, path):
            if state:
                WebEngine.WEB_MOUNTS[alias] = path
            elif WebEngine.WEB_MOUNTS.get(alias, False):
                del WebEngine.WEB_MOUNTS[alias]
        if modules is not None:
            # Set modules dir access
            _update(modules, "$modules", OSPath.MODULES)
        if data is not None:
            # Set data dir access
            _update(data, "$data", OSPath.DATA)
        if logs is not None:
            # Set logs dir access
            _update(logs, "$logs", OSPath.LOGS)
        return WebEngine.WEB_MOUNTS

    # =========================================
    # Static helpers for parsing
    # =========================================

    @staticmethod
    def _file_type(path:str) -> bytes:
        """File dynamic Content-Type handling"""
        # Extract the file extension
        ext = path.rsplit('.', 1)[-1].encode("ascii")
        # Return the content type based on the file extension
        return WebEngine.CONTENT_TYPES.get(ext, b"text/plain")

    @staticmethod
    def _parse_headers(raw_headers:memoryview) -> dict[str,str|int]:
        """
        Basic parser to extract HTTP/MIME headers
        :param raw_headers: headers
        """
        header_lines = bytes(raw_headers).split(b'\r\n')
        headers = {}
        for line in header_lines:
            # TODO: support for UTF-8 in field values (e.g filenames), can be board dependent
            if any(c > 127 for c in line):
                raise HeaderParsingError('Non-ASCII character found in the request')
            if b':' not in line:
                raise HeaderParsingError()
            name, value = line.split(b':', 1)
            name = name.strip().lower().decode("ascii")
            if name == "content-length":
                value = int(value.strip())
            else:
                value = value.strip().decode("ascii")
            headers[name] = value
        return headers

    @staticmethod
    def _is_multipart(headers:dict) -> str:
        """Determine from the headers if a request is multipart, and returns the boundary value"""
        if "content-type" in headers:
            multipart_regex = recompile('multipart/form-data\s*;\s*boundary\s*=\s*"?([^";\r\n]+)"?\s*')
            if (multipart_match := multipart_regex.match(headers['content-type'])):
                boundary = multipart_match.group(1).strip()
                return boundary if boundary else None

    @staticmethod
    def _parse_body_part(part:memoryview) -> tuple[dict, bytes]:
        """Parse part headers and body and return them as a tuple"""
        blank_idx = -1
        for i in range(len(part) - 3):
            if part[i:i+4] == b'\r\n\r\n':
                blank_idx = i
                break
        if blank_idx == -1:
            raise HeaderParsingError('Headers could not be parsed')
        headers = WebEngine._parse_headers(part[:blank_idx])
        body = part[blank_idx + 4:]
        return headers, body

    # =========================================
    # Helpers for engine_state machine termination
    # =========================================

    def terminate(self, status_code:int, content_type:bytes):
        """
        Terminate engine_state machine with status code and response content-type
        :param status_code: HTTP status code
        :param content_type: content-type of the response
        """
        self.engine_state = None
        self.status_code = status_code
        self.response_headers[b"content-type"] = content_type
        self.response_headers[b"connection"] = b"close"

    def _write_response_head(self, tx, content_length:int = None):
        """
        Write response status & header to the output,
        with optional content-length value
        """
        # Discard already accumulated content (e.g. 500 response on unexpected errors)
        tx.consume()
        tx.write(WebEngine.RESP_HEADERS[self.status_code])
        if content_length is not None:
            tx.write(b"\r\n")
            tx.write(b"content-length: %s" % str(content_length).encode("ascii"))
        for key, value in self.response_headers.items():
            tx.write(b"\r\n")
            tx.write(key)
            tx.write(b": ")
            tx.write(value)
        tx.write(b"\r\n\r\n")

    def _generate_response(self, tx, body:bytes|str|dict|tuple|list):
        """
        Write the complete response to the output, including status
        and headers. Return a BytesIO object if the content length
        exceeds the remaining buffer capacity, to delegate the writing
        of the response body to the transport layer.
        """
        if isinstance(body, (bytes, bytearray, memoryview)):
            self._write_response_head(tx, len(body))
            body_encoded = body
        elif isinstance(body, str):
            body_encoded = body.encode()
            self._write_response_head(tx, len(body_encoded))
        elif isinstance(body, (dict, tuple, list)):
            body_encoded = dumps(body).encode()
            self._write_response_head(tx, len(body_encoded))
        else:
            self.on_failure(tx, b"Unhandled body type")
            return
        if len(body_encoded) > tx.capacity - tx.size():
            return BytesIO(body_encoded)
        tx.write(body_encoded)

    def on_client_error(self, tx, info:bytes = b""):
        """Terminate state machine and write 400 response"""
        self.terminate(400, b"text/plain")
        response = b"Bad request" + b"\r\n" + info
        self._write_response_head(tx, len(response))
        tx.write(response)

    def on_missing_resource(self, tx, info:bytes = b""):
        """Terminate state machine and write 404 response"""
        self.terminate(404, b"text/plain")
        response = b"Not found" + b"\r\n" + info
        self._write_response_head(tx, len(response))
        tx.write(response)

    def on_timeout(self, tx):
        """Terminate state machine and write 408 response"""
        self.terminate(408, b"text/plain")
        response = b"Request timeout"
        self._write_response_head(tx, len(response))
        tx.write(response)

    def on_buffer_full(self, tx):
        """Terminate state machine and write 413 response"""
        self.terminate(413, b"text/plain")
        response = b"Content too large"
        self._write_response_head(tx, len(response))
        tx.write(response)

    def on_unsupported_media(self, tx, info:bytes = b""):
        """Terminate state machine and write 415 response"""
        self.terminate(415, b"text/plain")
        response = b"Unsupported media type" + b"\r\n" + info
        self._write_response_head(tx, len(response))
        tx.write(response)

    def on_failure(self, tx, info:bytes = b""):
        """Terminate state machine and write 500 response"""
        self.terminate(500, b"text/plain")
        response = b"Internal server error" + b"\r\n" + info
        self._write_response_head(tx, len(response))
        tx.write(response)

    def on_busy(self, tx):
        """Terminate state machine and write 503 response"""
        self.terminate(503, b"text/plain")
        response = b"Service unavailable"
        self._write_response_head(tx, len(response))
        tx.write(response)

    def on_unsupported_version(self, tx, version):
        """Terminate state machine and write 505 response"""
        self.terminate(505, b"text/plain")
        response = b"Unsupported version: " + version
        self._write_response_head(tx, len(response))
        tx.write(response)

    # ================================================================================
    # Parser states
    # - all states must handle rx and tx buffer arguments for reading and writing data
    # - mandatory methods/attributes of rx: find(), peek(), consume(), size()
    # - mandatory methods/attributes of tx: capacity, consume(), write(), size()
    # - rx/tx reference implementation: SlidingBuffer (Buffer.py)
    # ================================================================================

    def _parse_request_line_st(self, rx, tx):
        """State for parsing the request line"""
        status_line_sep = rx.find(b'\r\n')
        if status_line_sep == -1:
            return
        status_parts = bytes(rx.peek(status_line_sep)).split()
        if len(status_parts) != 3:
            if status_parts[0] not in self.METHODS:
                self.on_client_error(tx, b"Invalid request")
            else:
                self.on_client_error(tx, b"Malformed request line")
            return
        self.method = status_parts[0]
        self.url = status_parts[1].lstrip(b'/')
        self.version = status_parts[2]
        if self.method not in WebEngine.METHODS:
            self.on_client_error(tx, b"Unsupported method: %s" % self.method)
            return
        if self.version != b'HTTP/1.1':
            self.on_unsupported_version(tx, self.version)
            return
        rx.consume(status_line_sep + 2)
        self.engine_state = self._parse_headers_st

    def _parse_headers_st(self, rx, tx):
        """State for parsing headers"""
        if (blank_idx := rx.find(b'\r\n\r\n')) == -1:
            return
        try:
            self.headers = self._parse_headers(rx.peek(blank_idx))
        except HeaderParsingError:
            self.on_client_error(tx, b"Invalid headers")
            return
        rx.consume(blank_idx + 4)
        self.engine_state = self._route_request_st

    def _route_request_st(self, _, tx):
        """
        State for routing requests
        - supported ways: static resources, /rest, load module callbacks
        """
        if self.url.startswith(b'rest') and self.method == WebEngine.GET:
            self.engine_state = self._rest_api_st
            return
        if self.url in WebEngine.ENDPOINTS and \
            self.method in WebEngine.ENDPOINTS[self.url]:
            self.engine_state = self._lm_endpoint_st
            return
        if self.method == WebEngine.GET:
            resource = b'index.html' if not self.url else self.url
            extension = resource.rsplit(b'.', 1)[-1]
            if extension not in self.CONTENT_TYPES:
                if extension in (b"py", b"log", b"dat", b"cache"):
                    # Fallback to text/plain
                    self.CONTENT_TYPES[extension] = self.CONTENT_TYPES[b"txt"]
                else:
                    self.on_unsupported_media(tx, b"Not supported: %s" % extension)
                    return
            self.engine_state = lambda _rx, _tx: \
                self._send_file_st(_rx, _tx, resource.decode("ascii"))
            return
        self.on_client_error(tx)

    def _rest_api_st(self, _, tx):
        """State for processing load module commands through the /rest endpoint"""
        resp_schema = {'result': {}, 'state': False}
        cmd = self.url.decode("ascii").replace('rest', '', 1)
        if len(cmd) > 1:
            # TODO: create url_decode helper for: " ' >
            cmd = (cmd.replace('/', ' ').replace('-', ' ').replace("%3E", ">")
                .replace('%22', '"').replace('%E2%80%9C', '"').replace('%E2%80%9D', '"')
                .strip().split())
             # EXECUTE COMMAND - LoadModule
            if WebEngine.AUTH:
                if lm_is_loaded(cmd[0]):
                    state, out = lm_exec(cmd, jsonify=True)
                else:
                    state, out = (True, 'Auth:Protected')
            else:
                state, out = lm_exec(cmd, jsonify=True)
            try:
                # Load again ... hack for embedded json converter...
                resp_schema['result'] = loads(out)
            except:
                resp_schema['result'] = out
            resp_schema['state'] = state
        else:
            resp_schema['result'] = {"micrOS": WebEngine.VERSION,
                                     'node': cfgget('devfid'),
                                     'auth': WebEngine.AUTH}
            if len(tuple(WebEngine.ENDPOINTS.keys())) > 0:
                resp_schema['result']['usr_endpoints'] = tuple(
                    endpoint.decode("ascii") if isinstance(endpoint, (bytes, bytearray)) else endpoint
                    for endpoint in WebEngine.ENDPOINTS
                )
            resp_schema['state'] = True
        self.terminate(200, b"text/html")
        return self._generate_response(tx, resp_schema)

    def _lm_endpoint_st(self, rx, tx):
        """Process a request by registered load module callbacks"""
        callback =  WebEngine.ENDPOINTS[self.url][self.method]
        if "content-length" in self.headers and self.headers["content-length"] > 0:
            if mp_boundary := WebEngine._is_multipart(self.headers):
                self.mp_boundary = mp_boundary.encode("ascii")
                self.engine_state = self._start_multipart_parser_st
                return
            if self.headers["content-length"] > rx.size():
                return
            if self.headers["content-length"] < rx.size():
                self.on_client_error(tx, b"Content-length mismatch")
                return
            self.engine_state = None
            dtype, data = callback(self.headers, bytes(rx.peek()))
            dtype = dtype.encode("ascii")
        else:
            if not callable(callback):
                # Handle endpoint callback as a static resource
                self.engine_state = lambda _rx, _tx: self._send_file_st(_rx, _tx, callback)
                return
            dtype, data = callback(self.headers, b"")
            dtype = dtype.encode("ascii")
        # dtype:
        #   one-shot (simple MIME types): image/jpeg | text/html | text/plain
        #   - data contains the response to include in the body
        #
        #   task (streaming MIME types): multipart/x-mixed-replace | multipart/form-data
        #   - data must be: dict{callback,content-type}
        #     where callback is a function object without arguments, producing data
        #     in the format indicated by the content-type (e.g. image/jpeg | audio/l16;*)
        self.response_headers[b"content-type"] = dtype
        if dtype == b'image/jpeg':
            self.terminate(200, dtype)
            return self._generate_response(tx, data)
        elif dtype in (b'multipart/x-mixed-replace', b'multipart/form-data'):
            if type(data['callback']).__name__ not in ("function", "closure"):
                self.on_failure(tx, b"Invalid response handler")
                return
            self.terminate(200, dtype)
            boundary = b"micrOS_boundary"
            self.response_headers[b"content-type"] += b"; boundary=" + boundary
            self._write_response_head(tx)
            return WebEngine._multipart_wrapper_factory(
                data['callback'],
                data['content-type'].encode('ascii'),
                boundary
            )
        else:  # dtype: text/html or text/plain
            self.terminate(200, dtype)
            return self._generate_response(tx, data)

    @staticmethod
    def _multipart_wrapper_factory(callback,
                                   content_type:bytes,
                                   boundary:bytes):
        """
        Factory method for creating closures that write multipart responses
        :param callback: function without arguments, must return bytes-like objects
        :param content_type: content type of body parts
        :param boundary: boundary value
        :return closure: closure to invoke for response generation
        """
        boundary = b"--" + boundary
        content_type_header = b"content-type: %s\r\n\r\n" % content_type

        def _multipart_wrapper(tx):
            """
            Write multipart data generated from a callback's return value
            - if insufficient buffer space is available, the generator yields control so
            the caller can flush or drain the buffer
            :return bool: true if the stream is completed
            """
            while True:
                tx.write(boundary)
                part_body = callback()
                if not part_body:
                    tx.write(b"--")
                    yield True
                tx.write(b"\r\n")
                tx.write(content_type_header)
                written = 0
                while written < len(part_body):
                    to_write = tx.capacity - tx.size()
                    if not to_write:
                        raise BufferError("Cannot write multipart response to buffer")
                    tx.write(part_body[written:written + to_write])
                    written += to_write
                    yield False
                tx.write(b"\r\n")
        return _multipart_wrapper

    def _send_file_st(self, _, tx, web_resource: str):
        """State for returning a static resource"""
        err, web_resource = url_path_resolve(web_resource)
        if err:
            self.on_missing_resource(tx, b"Mount not found")
            return
        try:
            self.response_headers[b"content-length"] = str(stat(web_resource)[6]).encode()
            self.terminate(200, WebEngine._file_type(web_resource))
            self._write_response_head(tx)
            return open(web_resource, "rb")
        except OSError:
            self.on_missing_resource(tx)

    def _start_multipart_parser_st(self, rx, tx):
        """Initial state for processing multipart requests"""
        if not "content-length" in self.headers:
            self.on_client_error(tx, b"Missing content-length header")
            return
        if (start_delimiter := rx.find(b'\r\n')) == -1:
            return
        self.mp_delimiter = b'--' + self.mp_boundary + b'\r\n'
        self.mp_closing_delimiter = b'--' + self.mp_boundary + b'--'
        if rx.peek(start_delimiter + 2) != self.mp_delimiter:
            self.on_client_error(tx, b"Missing initial multipart boundary")
            return
        rx.consume(start_delimiter + 2)
        self.content_length_cnt += start_delimiter + 2
        self.engine_state = self._parse_boundary_st

    def _parse_boundary_st(self, rx, _):
        """State for parsing multipart boundary delimiter"""
        if rx.find(b'\r\n' + self.mp_delimiter) == -1 and \
            rx.find(b'\r\n' + self.mp_closing_delimiter) == -1:
            return
        self.engine_state = self._parse_complete_part_st

    def _parse_complete_part_st(self, rx, tx):
        """
        State for processing complete parts in a multipart request
        - registered load module callback is required to process parts
        """
        next_delimiter = rx.find(b'\r\n--' + self.mp_boundary)
        part = rx.peek(next_delimiter)
        rx.consume(next_delimiter + 2) # Consume leading CRLF
        self.content_length_cnt += next_delimiter + 2
        is_final = rx.peek(len(self.mp_closing_delimiter)) == self.mp_closing_delimiter
        # Validate part and content-length
        if self.headers["content-length"] < self.content_length_cnt:
            self.on_client_error(tx, b"Content-length mismatch")
            return
        try:
            part_headers, part_body = WebEngine._parse_body_part(part)
        except HeaderParsingError:
            self.on_client_error(tx, b"Invalid part headers")
            return
        callback = WebEngine.ENDPOINTS[self.url][self.method]
        # Process complete part
        if not is_final:
            callback(part_headers, part_body, first=self.mp_first_part, last=False)
            if rx.peek(len(self.mp_delimiter)) != self.mp_delimiter:
                self.on_client_error(tx, b"Invalid multipart boundary formatting")
                return
            rx.consume(len(self.mp_delimiter))
            self.content_length_cnt += len(self.mp_delimiter)
            self.mp_first_part = False
            self.engine_state = self._parse_boundary_st
            return
        # Process last part
        rx.consume(len(self.mp_closing_delimiter))
        self.content_length_cnt += len(self.mp_closing_delimiter)
        if self.headers["content-length"] != self.content_length_cnt and \
        self.content_length_cnt + rx.size() != self.headers["content-length"]:
            self.on_client_error(tx, b"Content-length mismatch")
            return
        dtype, data = callback(
            part_headers,
            part_body,
            first=self.mp_first_part,
            last=True)
        self.terminate(200, dtype.encode("ascii"))
        return self._generate_response(tx, data)
