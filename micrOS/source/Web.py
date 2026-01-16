"""
Module is responsible for webserver environment
dedicated to micrOS framework.
Built-in-function:
- response
    - landing page: index.html
    - rest/                                         - call load modules, e.x.: system/top
    - file response (.html, .css, .js, .jpeg)       - generic file server feature
    - "virtual" endpoints                           - to reply from script on a defined endpoint
        - stream                                    - stream data (jpeg) function

Designed by Marcell Ban aka BxNxM and szeka9 (GitHub)
"""

from re import compile
from json import dumps, loads
from uos import stat
import uasyncio as asyncio
from Tasks import lm_exec, NativeTask, lm_is_loaded
from Debug import syslog, console_write
from Config import cfgget
from Files import OSPath, path_join
try:
    from gc import mem_free, collect
except:
    from simgc import mem_free, collect  # simulator mode


class ServerBusyException(Exception):
    pass

class ConnectionError(Exception):
    pass

class HeaderDecodingError(Exception):
    pass

class WebEngine:
    __slots__ = ["client"]
    ENDPOINTS = {}
    AUTH = cfgget('auth')
    VERSION = "n/a"
    REQ200 = "HTTP/1.1 200 OK\r\nContent-Type: {dtype}\r\nContent-Length:{len}\r\n\r\n{data}"
    REQ200_CHUNKED = "HTTP/1.1 200 OK\r\nContent-Type: {dtype}\r\nTransfer-Encoding: chunked\r\n\r\n"
    REQ400 = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\nContent-Length: {len}\r\n\r\n{data}"
    REQ404 = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: {len}\r\n\r\n{data}"
    REQ500 = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\nContent-Length: {len}\r\n\r\n{data}"
    REQ503 = "HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/plain\r\nContent-Length: {len}\r\n\r\n{data}"
    CONTENT_TYPES = {"html": "text/html",
                     "css": "text/css",
                     "js": "application/javascript",
                     "json": "application/json",
                     "ico": "image/x-icon",             # favicon
                     "jpeg": "image/jpeg",
                     "png": "image/png",
                     "gif": "image/gif"}
    METHODS = ("GET", "POST", "DELETE")
    # MEMORY DIMENSIONING FOR THE BEST PERFORMANCE
    #         (is_limited, free_mem, min_mem_req_kb, chunk_threshold_kb, chunk_size_bytes)
    MEM_DIM = (None, -1, 20, 2, 1024)
    READ_TIMEOUT_SEC = 10

    def __init__(self, client, version):
        self.client = client
        WebEngine.VERSION = version

    async def a_send(self, response:str, encode:str='utf8'):
        raise NotImplementedError("Child class must implement a_send coroutine.")

    @staticmethod
    def file_type(path:str):
        """File dynamic Content-Type handling"""
        default_type = "text/plain"
        # Extract the file extension
        ext = path.rsplit('.', 1)[-1]
        # Return the content type based on the file extension
        return WebEngine.CONTENT_TYPES.get(ext, default_type)

    @staticmethod
    def parse_headers(raw_headers:bytes):
        """Basic parser to extract HTTP/MIME headers without guarantees on RFC compliance"""
        header_lines = raw_headers.decode('ascii').split('\r\n')
        headers = {}
        for line in header_lines:
            # TODO: support for UTF-8 in field values (e.g filenames), can be board dependent
            if any(ord(c) > 127 for c in line):
                raise HeaderDecodingError('Non-ASCII character found in the request')
            if ':' not in line:
                continue
            name, value = line.split(':', 1)
            headers[name.strip().lower()] = value.strip()
        return headers

    @staticmethod
    def dimensioning():
        #         (is_limited, free_mem, min_mem_req_kb, chunk_threshold_kb, chunk_size_bytes)
        if WebEngine.MEM_DIM[0] is None:
            collect()
            mfree = mem_free() // 1024   # <- bytes->kb
            if mfree < WebEngine.MEM_DIM[2]:
                # Too low memory - No Web UI - under 20kb
                WebEngine.MEM_DIM = (True, mfree) + WebEngine.MEM_DIM[2:]
                return WebEngine.MEM_DIM
            if mfree < WebEngine.MEM_DIM[2] * 5:
                # Normal: default memory setup - Web UI - under 100kb
                WebEngine.MEM_DIM = (False, mfree) + WebEngine.MEM_DIM[2:]
                return WebEngine.MEM_DIM
            # Large memory - Web UI - over 100kb
            upscale = max(1, min(25, int((mfree // WebEngine.MEM_DIM[2]) // 2)))  # ~50% free mem budget
            WebEngine.MEM_DIM = (False, mfree, WebEngine.MEM_DIM[2],
                                 WebEngine.MEM_DIM[3]*upscale, WebEngine.MEM_DIM[4]*upscale)
            syslog(f"[INFO] WebEngine ChunkUpscale ({upscale}x): {WebEngine.MEM_DIM}")
        return WebEngine.MEM_DIM

    async def response(self, request:bytes) -> bool:
        """HTTP GET/POST REQUEST - WEB INTERFACE"""
        # [0] PROTOCOL VALIDATION AND PARSING
        if not request:
            _err = "Empty request"
            await self.a_send(self.REQ400.format(len=len(_err), data=_err))
            return True
        status_line = request.split(b'\r\n', 1)[0]
        status_parts = status_line.decode('ascii').split()
        if len(status_parts) != 3:
            if status_parts[0] not in self.METHODS:
                # INVALID REQUEST - REQUEST OVERFLOW - NO RESPONSE
                syslog(f"[WARN] WebCli REQ Overflow: {len(status_parts)}")
                return False                    # Close connection...
            _err = "Malformed request line"
            await self.a_send(self.REQ400.format(len=len(_err), data=_err))
            return True
        _method, url, _version = status_parts
        if _method not in self.METHODS or not _version.startswith('HTTP/'):
            _err = f"Unsupported method: {_method} {_version}"
            await self.a_send(self.REQ400.format(len=len(_err), data=_err))
            return True
        payload = request[len(status_line):]
        blank_idx = payload.find(b'\r\n\r\n')
        try:
            if blank_idx > -1:
                headers = self.parse_headers(payload[0:blank_idx])
                body = payload[blank_idx + 4:]
            else:
                headers = self.parse_headers(payload)
                body = b''
        except HeaderDecodingError:
            await self.client.a_send(self.REQ400.format(len=18, data='400 Invalid Header'))
            return True
        # [1] REST API GET ENDPOINT [/rest]
        if url.startswith('/rest') and _method == "GET":
            self.client.console("[WebCli] --- /rest ACCEPT")
            try:
                await self.client.a_send(WebEngine.rest(url))
            except Exception as e:
                await self.client.a_send(self.REQ404.format(len=len(str(e)), data=e))
            return True
        # [2] DYNAMIC/USER ENDPOINTS (from Load Modules)
        if await self.endpoints(url, _method, headers, body):
            return True
        mem_limited, free, *_ = self.dimensioning()
        if mem_limited:
            _err = f"Low memory ({free} kb): serving API only."
            await self.a_send(self.REQ400.format(len=len(_err), data=_err))
            return True
        # [3] HOME/PAGE ENDPOINT(s) [default: / -> /index.html]
        if url.startswith('/') and _method == "GET":
            resource = 'index.html' if url == '/' else url.lstrip('/')
            web_resource = path_join(OSPath.WEB, resource)                  # Redirect path to web folder
            self.client.console(f"[WebCli] --- {url} ACCEPT -> {web_resource}")
            if "/" not in resource and resource.split('.')[-1] not in self.CONTENT_TYPES:
                # Validate /web root types only - otherwise default fallback type for unknowns: "text/plain"
                await self.client.a_send(self.REQ404.format(len=27, data='404 Not Supported File Type'))
                return True
            try:
                # SEND RESOURCE CONTENT: HTML, JS, CSS (WebEngine.CONTENT_TYPES)
                await self.file_transfer(web_resource)
            except OSError:
                await self.client.a_send(self.REQ404.format(len=13, data='404 Not Found'))
            except MemoryError as e:
                syslog(f"[ERR] WebCli {resource}: {e}")
                await self.client.a_send(self.REQ500.format(len=17, data='500 Out of Memory'))
            except Exception as e:
                syslog(f"[ERR] WebCli {resource}: {e}")
                await self.client.a_send(self.REQ500.format(len=16, data='500 Server Error'))
            return True
        # INVALID/BAD REQUEST
        await self.client.a_send(self.REQ400.format(len=15, data='400 Bad Request'))
        return True

    @staticmethod
    def rest(url):
        resp_schema = {'result': {}, 'state': False}
        cmd = url.replace('/rest', '')
        if len(cmd) > 1:
            # REST sub-parameter handling (rest commands)
            cmd = (cmd.replace('/', ' ').replace('-', ' ').replace("%3E", ">")
                   .replace('%22', '"').replace('%E2%80%9C', '"').replace('%E2%80%9D', '"')
                   .strip().split())
            # EXECUTE COMMAND - LoadModule
            if WebEngine.AUTH:
                state, out = lm_exec(cmd, jsonify=True) if lm_is_loaded(cmd[0]) else (True, 'Auth:Protected')
            else:
                state, out = lm_exec(cmd, jsonify=True)
            try:
                resp_schema['result'] = loads(out)  # Load again ... hack for embedded json converter...
            except:
                resp_schema['result'] = out
            resp_schema['state'] = state
        else:
            resp_schema['result'] = {"micrOS": WebEngine.VERSION, 'node': cfgget('devfid'), 'auth': WebEngine.AUTH}
            if len(tuple(WebEngine.ENDPOINTS.keys())) > 0:
                resp_schema['result']['usr_endpoints'] = tuple(WebEngine.ENDPOINTS)
            resp_schema['state'] = True
        response = dumps(resp_schema)
        return WebEngine.REQ200.format(dtype='text/html', len=len(response), data=response)

    async def endpoints(self, url:str, method:str, headers:dict, body:bytes):
        url = url[1:]  # Cut first / char
        if url in WebEngine.ENDPOINTS and method in WebEngine.ENDPOINTS[url]: # TODO: support for query parameters
            console_write(f"[WebCli] endpoint: {url}")
            # Registered endpoint was found - exec callback
            try:
                # RESOLVE ENDPOINT CALLBACK
                # dtype:
                #   one-shot (simple MIME types):    image/jpeg | text/html | text/plain              - data: raw
                #       task (streaming MIME types): multipart/x-mixed-replace | multipart/form-data  - data: dict{callback,content-type}
                #                                                                                       content-type: image/jpeg | audio/l16;*
                if body and (response := await self.handle_with_body(url, method, headers, body)):
                    dtype, data = response
                else:
                    # TODO: contract needed for passing headers
                    callback =  WebEngine.ENDPOINTS[url][method]
                    if callable(callback):
                        dtype, data = WebEngine.ENDPOINTS[url][method]()
                    else:
                        # Endpoint is a file reference under /web
                        web_resource = path_join(OSPath.WEB, callback)
                        await self.file_transfer(web_resource)
                        return True

                if dtype == 'image/jpeg':
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: {dtype}\r\nContent-Length:{len(data)}\r\n\r\n".encode('ascii') + data
                    await self.client.a_send(resp, encode=None)
                elif dtype in ('multipart/x-mixed-replace', 'multipart/form-data'):
                    resp_headers = f"HTTP/1.1 200 OK\r\nContent-Type: {dtype}; boundary=\"micrOS_boundary\"\r\n\r\n"
                    await self.client.a_send(resp_headers)
                    # Start Native stream async task
                    task = NativeTask()
                    tag=f"web.stream_{self.client.client_id.replace('W', '')}"
                    task.create(callback=self.stream(data['callback'], task, data['content-type']), tag=tag)
                else:  # dtype: text/html or text/plain
                    await self.client.a_send(WebEngine.REQ200.format(dtype=dtype, len=len(data), data=data))
            except ServerBusyException as e:
                await self.client.a_send(self.REQ503.format(len=len(str(e)), data=e))
            except HeaderDecodingError as e:
                await self.client.a_send(self.REQ400.format(len=len(str(e)), data=e))
            except Exception as e:
                if self.client.connected:
                    await self.client.a_send(self.REQ400.format(len=len(str(e)), data=e))
                syslog(f"[ERR] WebCli endpoints {url}: {e}")
            return True  # Registered endpoint was found and executed
        return False  # Not registered endpoint

    async def file_transfer(self, web_resource:str):
        """
        Send a file to the client using either normal or chunked HTTP transfer.
        :param web_resource: Path to the file to be served.
        """
        with open(web_resource, "rb") as file:
            chunking_threshold_kb = WebEngine.MEM_DIM[3]
            chunk_size_bytes = WebEngine.MEM_DIM[4]
            if stat(web_resource)[6] > chunking_threshold_kb * 1024:
                # Chunked HTTP transfer
                response = self.REQ200_CHUNKED.format(dtype=WebEngine.file_type(web_resource))
                await self.client.a_send(response)
                data = file.read(chunk_size_bytes)
                while data:
                    await self.client.a_send(f"{len(data):X}\r\n".encode(), None)
                    await self.client.a_send(data, None)
                    await self.client.a_send(b'\r\n', None)
                    data = file.read(chunk_size_bytes)
                await self.client.a_send(b'0\r\n\r\n', None)
                return
            # Normal HTTP transfer
            data = file.read()
            response = self.REQ200.format(dtype=WebEngine.file_type(web_resource), len=len(data), data="")
            await self.client.a_send(response)
            await self.client.a_send(data, None)

    async def stream(self, callback, task, content_type):
        """
        Async stream method.
        :param callback: sync or async function callback (auto-detect) WARNING: works for functions only (not methods!)
        :param task: NativeTask instance (that the stream runs in)
        :param content_type: image/jpeg | audio/l16;*
        """
        is_coroutine = 'generator' in str(type(callback))  # async function callback auto-detect
        with task:
            task.out = 'Stream started'
            data_to_send = b''

            while self.client.connected and data_to_send is not None:
                data_to_send = await callback() if is_coroutine else callback()
                part = (f"\r\n--micrOS_boundary\r\nContent-Type: {content_type}\r\n\r\n").encode('ascii') + data_to_send
                task.out = 'Data sent'
                await self.client.a_send(part, encode=None)
                await asyncio.sleep_ms(10)

            # Gracefully terminate the stream
            if self.client.connected:
                closing_boundary = '\r\n--micrOS_boundary--\r\n'
                await self.client.a_send(closing_boundary)
                await self.client.close()
            task.out = 'Finished stream'

    async def handle_with_body(self, url:str, method:str, headers:dict, body:bytes):
        """
        Handle requests with a body.
        :param url: synchronous function callback, expecting parts passed as bytes
        :param boundary: boundary parameter
        :param body: request body, handled depending on headers (e.g. content type)
        """
        content_length = int(headers.get("content-length", -1))
        is_multipart = False
        # [1] Header parsing
        if headers:
            if 'content-type' in headers:
                multipart_regex = compile("multipart/form-data;\s*boundary=\"?([^\";\r\n]+)\"?")
                if (multipart_match := multipart_regex.match(headers['content-type'])):
                    is_multipart = True
                    multipart_boundary = multipart_match.group(1).encode('ascii')
        # [2] Header dependent body handling
        if is_multipart:
            return await self.recv_multipart(WebEngine.ENDPOINTS[url][method], multipart_boundary, bytearray(body), content_length)
        # [3] Default handling
        # TODO: contract needed for passing headers
        return WebEngine.ENDPOINTS[url][method](body)

    async def recv_multipart(self, callback, boundary:bytes, part_buffer:bytearray, content_length:int):
        """
        Receives multipart body and runs a callback on each complete part.
        :param callback: synchronous callback function clb(part_headers, part_body), parsed headers and raw body
        :param boundary: boundary parameter
        :param part_buffer: contains initial request body, remaining parts are read if the body contains no closing delimiter
        :param content_length: content length number
        """
        dtype = 'text/plain'
        data = 'failed to parse'
        delimiter = b'--' + boundary
        delimiter_line = delimiter + b'\r\n'
        close_delimiter = delimiter + b'--'
        at_start = True
        first_part = True
        actual_length = len(part_buffer)

        if content_length <= 0:
            raise ValueError("Invalid content-length")

        async def read_more():
            error, more = await self.client.read(decoding=None, timeout_seconds=self.READ_TIMEOUT_SEC)
            if error:
                await self.client.close()
                raise ConnectionError()
            if not more:
                raise ValueError('Unexpected EOF in multipart body')
            return more

        def parse_part(part:bytes):
            blank_idx = part.find(b'\r\n\r\n')
            if blank_idx == -1:
                raise ValueError('Headers could not be parsed')
            headers = self.parse_headers(part[:blank_idx])
            body = part[blank_idx + 4:]
            return headers, body

        while True:
            # [1] Read until a complete part is received
            while b'\r\n' not in part_buffer:
                more = await read_more()
                if actual_length + len(more) > content_length:
                    raise ValueError('Invalid content-length')
                part_buffer += more
                actual_length += len(more)
            if at_start:
                if not part_buffer.startswith(delimiter_line):
                    raise ValueError('Missing initial multipart boundary')
                part_buffer = part_buffer[len(delimiter_line):]
                at_start = False
                continue
            idx = part_buffer.find(b'\r\n' + delimiter)
            if idx == -1:
                more = await read_more()
                if actual_length + len(more) > content_length:
                    raise ValueError('Invalid content-length')
                part_buffer += more
                actual_length += len(more)
                continue
            # [2] Complete part received
            part = part_buffer[:idx]
            part_buffer = part_buffer[idx + 2:]  # Consume leading CRLF
            if part_buffer.startswith(close_delimiter):
                # Last part found, stop processing delimiters
                if part:
                    part_headers, part_body = parse_part(part)
                    dtype, data = callback(part_headers, part_body, first=first_part, last=True)
                break
            if not part_buffer.startswith(delimiter_line):
                raise ValueError('Invalid multipart boundary formatting')
            part_buffer = part_buffer[len(delimiter_line):]
            if part:
                # Process complete part
                part_headers, part_body = parse_part(part)
                dtype, data = callback(part_headers, part_body, first=first_part)
                first_part = False
        # [3] Verify content length
        if actual_length < content_length:
            more = await read_more()
            if actual_length + len(more) != content_length:
                raise ValueError('Invalid content-length')
            # Ignore remaining content
        return dtype, data
