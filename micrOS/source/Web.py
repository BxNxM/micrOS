from json import dumps, loads
import uasyncio as asyncio
from Tasks import lm_exec, NativeTask, lm_is_loaded
from Debug import errlog_add, console_write
from Config import cfgget


class WebEngine:
    __slots__ = ["client"]
    REST_ENDPOINTS = {}
    AUTH = cfgget('auth')
    VERSION = "n/a"
    REQ200 = "HTTP/1.1 200 OK\r\nContent-Type: {dtype}\r\nContent-Length:{len}\r\n\r\n{data}"
    REQ400 = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\nContent-Length: {len}\r\n\r\n{data}"
    REQ404 = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: {len}\r\n\r\n{data}"

    def __init__(self, client, version):
        self.client = client
        WebEngine.VERSION = version

    @staticmethod
    def file_type(path):
        """File dynamic Content-Type handling"""
        content_types = {".html": "text/html",
                         ".css": "text/css",
                         ".js": "application/javascript"}
        # Extract the file extension
        ext = path.rsplit('.', 1)[-1]
        # Return the content type based on the file extension
        return content_types.get(f".{ext}", "text/plain")

    async def response(self, request):
        """HTTP GET REQUEST - WEB INTERFACE"""
        # Parse request line (first line)
        _method, url, _version = request.split('\n')[0].split()
        # Protocol validation
        if _method != "GET" and _version.startswith('HTTP'):
            _err = "Bad Request: not GET HTTP/1.1"
            await self.client.a_send(self.REQ400.format(len=len(_err), data=_err))
            return

        # [1] REST API GET ENDPOINT [/rest]
        if url.startswith('/rest'):
            self.client.console("[WebCli] --- /rest ACCEPT")
            try:
                await self.client.a_send(WebEngine.rest(url))
            except Exception as e:
                await self.client.a_send(self.REQ404.format(len=len(str(e)), data=e))
            return
        # [2] DYNAMIC/USER ENDPOINTS (from Load Modules)
        if await self.endpoints(url):
            return
        # [3] HOME/PAGE ENDPOINT(s) [default: / -> /index.html]
        if url.startswith('/'):
            resource = 'index.html' if url == '/' else url.replace('/', '')
            self.client.console(f"[WebCli] --- {url} ACCEPT")
            if resource.split('.')[-1] not in ('html', 'js', 'css'):
                await self.client.a_send(self.REQ404.format(len=27, data='404 Not supported file type'))
                return
            try:
                # SEND RESOURCE CONTENT: HTML, JS, CSS
                with open(resource, 'r') as file:
                    html = file.read()
                await self.client.a_send(self.REQ200.format(dtype=WebEngine.file_type(resource), len=len(html), data=html))
            except OSError:
                await self.client.a_send(self.REQ404.format(len=13, data='404 Not Found'))
            return
        # INVALID/BAD REQUEST
        await self.client.a_send(self.REQ400.format(len=15, data='400 Bad Request'))

    @staticmethod
    def rest(url):
        resp_schema = {'result': None, 'state': False}
        cmd = url.replace('/rest', '')
        if len(cmd) > 1:
            # REST sub-parameter handling (rest commands)
            cmd = (cmd.replace('/', ' ').replace('%22', '"').replace('%E2%80%9C', '"')
                   .replace('%E2%80%9D', '"').replace('-', ' ').strip().split())
            # request json format instead of default string output (+ handle & tasks syntax)
            cmd.insert(-1, '>json') if cmd[-1].startswith('&') else cmd.append('>json')
            # EXECUTE COMMAND - LoadModule
            if WebEngine.AUTH:
                state, out = lm_exec(cmd) if lm_is_loaded(cmd[0]) or cmd[0].startswith('modules') else (
                True, 'Auth:Protected')
            else:
                state, out = lm_exec(cmd)
            try:
                resp_schema['result'] = loads(out)  # Load again ... hack for embedded shell json converter...
            except:
                resp_schema['result'] = out
            resp_schema['state'] = state
        else:
            resp_schema['result'] = {"micrOS": WebEngine.VERSION, 'node': cfgget('devfid'), 'auth': WebEngine.AUTH}
            if len(tuple(WebEngine.REST_ENDPOINTS.keys())) > 0:
                resp_schema['result']['usr_endpoints'] = tuple(WebEngine.REST_ENDPOINTS)
            resp_schema['state'] = True
        response = dumps(resp_schema)
        return WebEngine.REQ200.format(dtype='text/html', len=len(response), data=response)

    async def endpoints(self, url):
        url = url[1:]  # Cut first / char
        if url in WebEngine.REST_ENDPOINTS:
            console_write(f"[WebCli] endpoint: {url}")
            # Registered endpoint was found - exec callback
            try:
                # RESOLVE ENDPOINT CALLBACK
                # dtype:
                #   one-shot: image/jpeg | text/html | text/plain              - data: raw
                #       task: multipart/x-mixed-replace | multipart/form-data  - data: dict=callback,content-type
                #                   content-type: image/jpeg | audio/l16;*
                dtype, data = WebEngine.REST_ENDPOINTS[url]()
                if dtype == 'image/jpeg':
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: {dtype}\r\nContent-Length:{len(data)}\r\n\r\n".encode(
                        'utf8') + data
                    await self.client.a_send(resp, encode=None)
                elif dtype in ('multipart/x-mixed-replace', 'multipart/form-data'):
                    headers = (
                        f"HTTP/1.1 200 OK\r\nContent-Type: {dtype}; boundary=\"micrOS_boundary\"\r\n\r\n").encode(
                        'utf-8')
                    await self.client.a_send(headers, encode=None)
                    # Start Native stream async task
                    task = NativeTask()
                    task.create(callback=self.stream(data['callback'], task, data['content-type']),
                                tag=f"web.stream_{self.client.client_id.replace('W', '')}")
                else:  # dtype: text/html or text/plain
                    await self.client.a_send(
                        f"HTTP/1.1 200 OK\r\nContent-Type: {dtype}\r\nContent-Length:{len(data)}\r\n\r\n{data}")
            except Exception as e:
                await self.client.a_send(self.REQ404.format(len=len(str(e)), data=e))
                errlog_add(f"[ERR] WebCli endpoints {url}: {e}")
            return True  # Registered endpoint was found and executed
        return False  # Not registered endpoint

    async def stream(self, callback, task, content_type):
        """
        Async stream method
        :param callback: sync or async function callback (auto-detect) WARNING: works for functions only (not methods!)
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
                await self.client.a_send(closing_boundary, encode=None)
                await self.client.close()
            task.out = 'Finished stream'