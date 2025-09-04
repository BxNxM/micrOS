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

from json import dumps, loads
import uasyncio as asyncio
from Tasks import lm_exec, NativeTask, lm_is_loaded
from Debug import syslog, console_write
from Config import cfgget
from Files import OSPath, path_join
try:
    from gc import mem_free, collect
except:
    from simgc import mem_free, collect  # simulator mode


class WebEngine:
    __slots__ = ["client"]
    ENDPOINTS = {}
    AUTH = cfgget('auth')
    VERSION = "n/a"
    REQ200 = "HTTP/1.1 200 OK\r\nContent-Type: {dtype}\r\nContent-Length:{len}\r\n\r\n{data}"
    REQ400 = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\nContent-Length: {len}\r\n\r\n{data}"
    REQ404 = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: {len}\r\n\r\n{data}"
    CONTENT_TYPES = {"html": "text/html",
                     "css": "text/css",
                     "js": "application/javascript",
                     "json": "application/json",
                     "ico": "image/x-icon",             # favicon
                     "jpeg": "image/jpeg",
                     "png": "image/png",
                     "gif": "image/gif"}
    METHODS = ("GET", "POST")
    MEM_LIMITED = (None, 0)

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
    def is_mem_limited() -> (bool, int):
        """Check if memory is limited for the FE"""
        if WebEngine.MEM_LIMITED[0] is None:
            collect()
            mfree = int(mem_free() * 0.001)
            WebEngine.MEM_LIMITED = (mfree < 50, mfree)        # 50 kb memory requirement
        return WebEngine.MEM_LIMITED

    async def response(self, request:str) -> bool:
        """HTTP GET/POST REQUEST - WEB INTERFACE"""
        # [0] PROTOCOL VALIDATION AND PARSING
        lines = request.splitlines()
        if not lines:
            _err = "Empty request"
            await self.a_send(self.REQ400.format(len=len(_err), data=_err))
            return True
        request_parts = lines[0].split()
        if len(request_parts) != 3:
            if request_parts[0] not in self.METHODS:
                # INVALID REQUEST - REQUEST OVERFLOW - NO RESPONSE
                syslog(f"[WARN] WebCli REQ Overflow: {len(lines[0])}")
                return False                    # Close connection...
            _err = "Malformed request line"
            await self.a_send(self.REQ400.format(len=len(_err), data=_err))
            return True
        _method, url, _version = request_parts
        if _method not in self.METHODS or not _version.startswith('HTTP/'):
            _err = f"Unsupported method: {_method} {_version}"
            await self.a_send(self.REQ400.format(len=len(_err), data=_err))
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
        payload = lines if _method == "POST" else []
        if await self.endpoints(url, _method, payload):
            return True
        mem_limited, free = self.is_mem_limited()
        if mem_limited:
            _err = f"Low memory ({free} kb): serving API only."
            await self.a_send(self.REQ400.format(len=len(_err), data=_err))
            return True
        # [3] HOME/PAGE ENDPOINT(s) [default: / -> /index.html]
        if url.startswith('/') and _method == "GET":
            resource = 'index.html' if url == '/' else url.replace('/', '')
            web_resource = path_join(OSPath.WEB, resource)                  # Redirect path to web folder
            self.client.console(f"[WebCli] --- {url} ACCEPT -> {web_resource}")
            if resource.split('.')[-1] not in tuple(self.CONTENT_TYPES.keys()):
                await self.client.a_send(self.REQ404.format(len=27, data='404 Not supported file type'))
                return True
            try:
                # SEND RESOURCE CONTENT: HTML, JS, CSS (WebEngine.CONTENT_TYPES)
                with open(web_resource, 'r') as file:
                    data = file.read()
                response = self.REQ200.format(dtype=WebEngine.file_type(resource), len=len(data), data=data)
                # Send entire response data (implement chunking if necessary)
                await self.client.a_send(response)
            except Exception as e:
                if 'memory allocation failed' in str(e):
                    syslog(f"[ERR] WebCli {resource}: {e}")
                await self.client.a_send(self.REQ404.format(len=13, data='404 Not Found'))
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

    async def endpoints(self, url:str, method:str, payload:list):
        url = url[1:]  # Cut first / char
        if url in WebEngine.ENDPOINTS and method in WebEngine.ENDPOINTS[url]:
            console_write(f"[WebCli] endpoint: {url}")
            # Registered endpoint was found - exec callback
            try:
                # RESOLVE ENDPOINT CALLBACK
                # dtype:
                #   one-shot (simple MIME types):    image/jpeg | text/html | text/plain              - data: raw
                #       task (streaming MIME types): multipart/x-mixed-replace | multipart/form-data  - data: dict{callback,content-type}
                #                                                                                       content-type: image/jpeg | audio/l16;*
                if method == "POST":
                    try:
                        blank_index = payload.index("")
                        body_lines = payload[blank_index + 1:]
                    except ValueError:
                        body_lines = []
                    dtype, data = WebEngine.ENDPOINTS[url][method]("\n".join(body_lines))
                else:
                    dtype, data = WebEngine.ENDPOINTS[url][method]()

                if dtype == 'image/jpeg':
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: {dtype}\r\nContent-Length:{len(data)}\r\n\r\n".encode('utf8') + data
                    await self.client.a_send(resp, encode=None)
                elif dtype in ('multipart/x-mixed-replace', 'multipart/form-data'):
                    headers = f"HTTP/1.1 200 OK\r\nContent-Type: {dtype}; boundary=\"micrOS_boundary\"\r\n\r\n"
                    await self.client.a_send(headers)
                    # Start Native stream async task
                    task = NativeTask()
                    tag=f"web.stream_{self.client.client_id.replace('W', '')}"
                    task.create(callback=self.stream(data['callback'], task, data['content-type']), tag=tag)
                else:  # dtype: text/html or text/plain
                    await self.client.a_send(WebEngine.REQ200.format(dtype=dtype, len=len(data), data=data))
            except Exception as e:
                await self.client.a_send(self.REQ404.format(len=len(str(e)), data=e))
                syslog(f"[ERR] WebCli endpoints {url}: {e}")
            return True  # Registered endpoint was found and executed
        return False  # Not registered endpoint

    async def stream(self, callback, task, content_type):
        """
        Async stream method
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
                part = (f"\r\n--micrOS_boundary\r\nContent-Type: {content_type}\r\n\r\n").encode('utf-8') + data_to_send
                task.out = 'Data sent'
                await self.client.a_send(part, encode=None)
                await asyncio.sleep_ms(10)

            # Gracefully terminate the stream
            if self.client.connected:
                closing_boundary = '\r\n--micrOS_boundary--\r\n'
                await self.client.a_send(closing_boundary)
                await self.client.close()
            task.out = 'Finished stream'
