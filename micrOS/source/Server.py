"""
Module is responsible for socket server
dedicated to micrOS framework.
- The heart of communication
- providing server-client console instance

Designed by Marcell Ban aka BxNxM GitHub
"""
#########################################################
#                         IMPORTS                       #
#########################################################

import uasyncio as asyncio
from utime import ticks_ms, ticks_diff
from Config import cfgget
from Debug import console_write, errlog_add
from Network import ifconfig
from Tasks import Manager
from Shell import Shell
try:
    from gc import collect
except:
    console_write("[SIMULATOR MODE GC IMPORT]")
    from simgc import collect

# Module load optimization, needed only for webui
if cfgget('webui'):
    from json import dumps, loads
    from Tasks import lm_exec, NativeTask, lm_is_loaded


#########################################################
#         SOCKET SERVER-CLIENT HANDLER CLASSES          #
#           Client (Base), ShellCli, WebCli             #
#########################################################

class Client:
    ACTIVE_CLIS = {}
    INDENT = 0

    def __init__(self, reader, writer, r_size):
        """
        Base class for async client handling
        :param reader: async reader stream object
        :param writer: async writer stream object
        :param r_size: async socket read size
        """
        self.connected = True
        self.reader = reader
        self.writer = writer
        self.read_bytes = r_size       # bytes to read on async socket (default: micrOS shell size)
        # Set client ID
        client_id = writer.get_extra_info('peername')
        self.client_id = f"{type(self).__name__[0]}{'.'.join(client_id[0].split('.')[-2:])}:{str(client_id[1])}"
        self.last_msg_t = ticks_ms()

    @staticmethod
    def console(msg):
        console_write("|" + "-" * Client.INDENT + msg)
        Client.INDENT += 1 if Client.INDENT < 50 else 0       # Auto indent

    async def read(self):
        """
        [Base] Implements client read function, reader size: 2048
        - set timeout counter
        - read input from client (run: return False)
        - connection error handling (stop: return True)
        - exit command handling (stop: return True)
        """
        Client.console(f"[Client] read {self.client_id}")
        self.last_msg_t = ticks_ms()
        try:
            request = await self.reader.read(self.read_bytes)
            request = request.decode('utf8').strip()
        except Exception as e:
            Client.console(f"[Client] Stream read error ({self.client_id}): {e}")
            collect()           # gc collection: "fix" for memory allocation failed, allocating 2049 bytes
            return True, ''

        # Input handling
        Client.console(f"[Client] raw request ({self.client_id}): |{request}|")
        if request in ('exit', ''):
            return True, request
        return False, request

    async def a_send(self, response, encode='utf8'):
        """
        [Base] Async socket send method
        """
        if self.connected:
            # Client.console(f"[Client] ----- SteamWrite: {response}")
            # Store data in stream buffer... then drain
            try:
                self.writer.write(response if encode is None else response.encode(encode))
            except Exception as e:
                # Maintain ACTIVE_CLIS - remove closed connection by peer.
                await self.close()
                errlog_add(f"[WARN] Client.a_send (auto-drop) {self.client_id}: {e}")
                return          # Abort async send (no drain)
            # Send buffered data with async task - hacky
            try:
                # Send write buffer
                # Client.console("  |----- start drain")
                await self.writer.drain()
                # Client.console("  |------ stop drain")
            except Exception as e:
                Client.console(f"[Client] Drain error -> close conn: {e}")
                await self.close()
        else:
            console_write("[Client] NoCon: response>dev/nul")

    def send(self, response):
        # Implement in child class - synchronous send method
        pass

    async def close(self):
        """
        [Base] Async socket close method
        """
        Client.console(f"[Client] Close connection {self.client_id}")
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception as e:
            Client.console(f"[Client] Close error {self.client_id}: {e}")
        self.connected = False
        Client.INDENT = 0
        # Maintain ACTIVE_CLIS - remove closed connection by peer.
        Client.drop_client(self.client_id)
        # gc.collect()
        collect()

    @staticmethod
    def drop_client(client_id):
        """
        [Base] Generic client connection remove from task cache
        """
        if Client.ACTIVE_CLIS.get(client_id, None) is not None:
            Client.ACTIVE_CLIS.pop(client_id)
        # Update server task output (? test ?)
        Manager().server_task_msg(','.join(list(Client.ACTIVE_CLIS)))

    def __del__(self):
        """Client GC collect"""
        collect()
        Client.console(f"[Client] del: {self.client_id}")


class WebCli(Client):
    REST_ENDPOINTS = {}
    AUTH = cfgget('auth')
    REQ200 = "HTTP/1.1 200 OK\r\nContent-Type: {dtype}\r\nContent-Length:{len}\r\n\r\n{data}"
    REQ400 = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\nContent-Length: {len}\r\n\r\n{data}"
    REQ404 = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: {len}\r\n\r\n{data}"

    def __init__(self, reader, writer):
        Client.__init__(self, reader, writer, r_size=512)

    async def run_web(self):
        # Update server task output
        Manager().server_task_msg(','.join(list(Client.ACTIVE_CLIS)))

        # Run async connection handling
        while self.connected:
            try:
                # Read request msg from client
                state, request = await self.read()
                if state:
                    break
                await self.response(request)
            except Exception as e:
                errlog_add(f"[ERR] Client.run_web: {e}")
                break
        # Close connection
        await self.close()

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
            await self.a_send(self.REQ400.format(len=len(_err), data=_err))
            return

        # [1] REST API GET ENDPOINT [/rest]
        if url.startswith('/rest'):
            Client.console("[WebCli] --- /rest ACCEPT")
            try:
                await self.a_send(WebCli.rest(url))
            except Exception as e:
                await self.a_send(self.REQ404.format(len=len(str(e)), data=e))
            return
        # [2] DYNAMIC/USER ENDPOINTS (from Load Modules)
        if await self.endpoints(url):
            return
        # [3] HOME/PAGE ENDPOINT(s) [default: / -> /index.html]
        if url.startswith('/'):
            resource = 'index.html' if url == '/' else url.replace('/', '')
            Client.console(f"[WebCli] --- {url} ACCEPT")
            if resource.split('.')[-1] not in ('html', 'js', 'css'):
                await self.a_send(self.REQ404.format(len=27, data='404 Not supported file type'))
                return
            try:
                # SEND RESOURCE CONTENT: HTML, JS, CSS
                with open(resource, 'r') as file:
                    html = file.read()
                await self.a_send(self.REQ200.format(dtype=WebCli.file_type(resource), len=len(html), data=html))
            except OSError:
                await self.a_send(self.REQ404.format(len=13, data='404 Not Found'))
            return
        # INVALID/BAD REQUEST
        await self.a_send(self.REQ400.format(len=15, data='400 Bad Request'))

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
            if WebCli.AUTH:
                state, out = lm_exec(cmd) if lm_is_loaded(cmd[0]) or cmd[0].startswith('modules') else (True, 'Auth:Protected')
            else:
                state, out = lm_exec(cmd)
            try:
                resp_schema['result'] = loads(out)       # Load again ... hack for embedded shell json converter...
            except:
                resp_schema['result'] = out
            resp_schema['state'] = state
        else:
            resp_schema['result'] = {"micrOS": Shell.MICROS_VERSION, 'node': cfgget('devfid'), 'auth': WebCli.AUTH}
            if len(tuple(WebCli.REST_ENDPOINTS.keys())) > 0:
                resp_schema['result']['usr_endpoints'] = tuple(WebCli.REST_ENDPOINTS)
            resp_schema['state'] = True
        response = dumps(resp_schema)
        return WebCli.REQ200.format(dtype='text/html', len=len(response), data=response)

    @staticmethod
    def register(endpoint, callback):
        # AUTO ENABLE webui when register (endpoint) called and webui is False
        if not cfgget('webui'):
            from Config import cfgput
            if cfgput('webui', True):        # SET webui to True
                from machine import reset
                reset()                                 # HARD RESET (REBOOT)
        WebCli.REST_ENDPOINTS[endpoint] = callback

    async def endpoints(self, url):
        url = url[1:]       # Cut first / char
        if url in WebCli.REST_ENDPOINTS:
            console_write(f"[WebCli] endpoint: {url}")
            # Registered endpoint was found - exec callback
            try:
                # RESOLVE ENDPOINT CALLBACK
                # dtype:
                #   one-shot: image/jpeg | text/html | text/plain              - data: raw
                #       task: multipart/x-mixed-replace | multipart/form-data  - data: dict=callback,content-type
                #                   content-type: image/jpeg | audio/l16;*
                dtype, data = WebCli.REST_ENDPOINTS[url]()
                if dtype == 'image/jpeg':
                    resp = f"HTTP/1.1 200 OK\r\nContent-Type: {dtype}\r\nContent-Length:{len(data)}\r\n\r\n".encode('utf8') + data
                    await self.a_send(resp, encode=None)
                elif dtype in ('multipart/x-mixed-replace', 'multipart/form-data'):
                    headers = (f"HTTP/1.1 200 OK\r\nContent-Type: {dtype}; boundary=\"micrOS_boundary\"\r\n\r\n").encode('utf-8')
                    await self.a_send(headers, encode=None)
                    # Start Native stream async task
                    task = NativeTask()
                    task.create(callback=self.stream(data['callback'], task, data['content-type']),
                                tag=f"web.stream_{self.client_id.replace('W', '')}")
                else:  # dtype: text/html or text/plain
                    await self.a_send(f"HTTP/1.1 200 OK\r\nContent-Type: {dtype}\r\nContent-Length:{len(data)}\r\n\r\n{data}")
            except Exception as e:
                await self.a_send(self.REQ404.format(len=len(str(e)), data=e))
                errlog_add(f"[ERR] WebCli endpoints {url}: {e}")
            return True         # Registered endpoint was found and executed
        return False            # Not registered endpoint

    async def stream(self, callback, task, content_type):
        """
        Async stream method
        :param callback: sync or async function callback (auto-detect) WARNING: works for functions only (not methods!)
        """
        is_coroutine = 'generator' in str(type(callback))   # async function callback auto-detect
        with task:
            task.out = 'Stream started'
            data_to_send = b''

            while self.connected and data_to_send is not None:
                data_to_send = await callback() if is_coroutine else callback()
                part = (f"\r\n--micrOS_boundary\r\nContent-Type: {content_type}\r\n\r\n").encode('utf-8') + data_to_send
                task.out = 'Data sent'
                await self.a_send(part, encode=None)
                await asyncio.sleep_ms(10)

            # Gracefully terminate the stream
            if self.connected:
                closing_boundary = '\r\n--micrOS_boundary--\r\n'
                await self.a_send(closing_boundary, encode=None)
                await self.close()
            task.out = 'Finished stream'


class ShellCli(Client, Shell):

    def __init__(self, reader, writer):
        Client.__init__(self, reader, writer, r_size=2048)          # r_size: 2048 default on ShellCli!
        Client.console(f"[ShellCli] new conn: {self.client_id}")
        self.drain_event = asyncio.Event()
        self.drain_event.set()
        Shell.__init__(self)

    def send(self, response):
        """
        Send response to client with non-async function
        """
        if self.connected:
            if self.prompt() != response:
                # [format] Add new line if not prompt
                response = f"{response}\n"
            # Client.console("f[Client] ----- SteamWrite: {response}")
            # Store data in stream buffer
            try:
                self.writer.write(response.encode('utf8'))
            except:
                # Maintain ACTIVE_CLIS - remove closed connection by peer.
                Client.drop_client(self.client_id)
                errlog_add(f"[WARN] ShellCli.send (auto-drop) {self.client_id}")
            # Send buffered data with async task - hacky
            if self.drain_event.is_set():
                self.drain_event.clear()        # set drain busy (False)
                asyncio.get_event_loop().create_task(self.__wait_for_drain())
        else:
            console_write(f"[ShellCli] NoCon: response>/dev/nul")

    async def __wait_for_drain(self):
        """
        Handle drain serialization
        - solve output data duplicate
        """
        try:
            # send write buffer
            # Client.console("  |----- start drain")
            await self.writer.drain()
            # Client.console("  |------ stop drain")
        except Exception as e:
            Client.console(f"[ShellCli] Drain error -> close conn: {e}")
            await self.close()
        # set drain free
        self.drain_event.set()                  # set drain free (True)

    async def close(self):
        Client.console(f"[ShellCli] Close connection {self.client_id}")
        self.send("Bye!\n")
        # Reset shell state machine
        self.reset()
        await asyncio.sleep_ms(50)
        # Used from Client parent class
        await super().close()

    async def __shell_cmd(self, request):
        """
        Handle micrOS shell commands
        """
        # Run micrOS shell with request string
        try:
            # Handle micrOS shell
            Client.console("[ShellCli] --- #Run shell")
            state = self.shell(request)
            if state:
                return False      # exit_loop
            return True           # exit_loop : Close session when shell returns False (auth Failed, etc.)
        except Exception as e:
            Client.console(f"[ShellCli] Shell exception: {e}")
            if "ECONNRESET" in str(e):
                return True       # exit_loop
        self.send("[HA] Critical error - disconnect & hard reset")
        errlog_add("[ERR] Socket critical error - reboot")
        self.reboot()

    async def run_shell(self):
        # Update server task output
        Manager().server_task_msg(','.join(list(Client.ACTIVE_CLIS)))
        # Init prompt
        self.send(self.prompt())
        # Run async connection handling
        while self.connected:
            try:
                # Read request msg from client
                state, request = await self.read()
                if state:
                    break
                _exit = await self.__shell_cmd(request)
                if _exit:
                    collect()
                    break
            except Exception as e:
                errlog_add(f"[ERR] handle_client: {e}")
                break
        # Close connection
        await self.close()


#########################################################
#                    SOCKET SERVER CLASS                #
#########################################################

class SocketServer:
    """
    Socket message data packet layer - send and receive
    Embedded command interpretation:
    - exit
    Handle user requests/commands with Shell (bash like experience)
    """
    __instance = None

    def __new__(cls):
        """
        Singleton design pattern
        __new__ - Customize the instance creation
        cls     - class
        """
        if not cls.__instance:
            # SocketServer singleton properties
            cls.__instance = super(SocketServer, cls).__new__(cls)
            cls.__instance._initialized = False
        return cls.__instance

    def __init__(self):
        if not self._initialized:
            # Socket server initial parameters
            self.server = None                       # ShellCli server instance
            self.web = None                          # WebCli server instance
            self._host = '0.0.0.0'                   # listens on all available interfaces
            _queue = cfgget('aioqueue')              # CONNECTION QUEUE SIZE, common for both interface
            self._socqueue = 3 if _queue < 3 else _queue

            # ---- Config ---
            self._port = cfgget("socport")
            # ---- Set socket timeout (min 5 sec!!! hardcoded)
            soc_timeout = int(cfgget("soctout"))
            self._timeout = 5 if soc_timeout < 5 else soc_timeout
            # ---         ----
            self._initialized = True
            Client.console("[ socket server ] <<constructor>>")

    #####################################
    #       Socket Server Methods       #
    #####################################

    async def accept_client(self, new_client):
        """
        Client handler
        - check active connection timeouts
        - accept new if fits in queue
        :param new_client: new Client class object
        """
        # Get new client ID
        new_client_id = new_client.client_id
        # Add new client immediately if queue not full
        if len(list(Client.ACTIVE_CLIS.keys())) < self._socqueue:
            # Add new client to active clients dict
            Client.ACTIVE_CLIS[new_client_id] = new_client
            return True                     # [!] Enable new connection

        # Get active clients timeout counters - handle new client depending on active client timeouts
        Client.console(f"NEW CLIENT CONN: {new_client_id}")
        for cli_id, cli in Client.ACTIVE_CLIS.items():
            cli_inactive = int(ticks_diff(ticks_ms(), cli.last_msg_t) * 0.001)
            Client.console(f"[server] accept new {new_client_id} - active {cli_id} tout:{self._timeout - cli_inactive}s")
            if not cli.connected or cli_inactive > self._timeout:
                # OPEN CONNECTION IS INACTIVE > CLOSE
                Client.console("------- client timeout - accept new connection")
                await cli.close()
                return True                 # [!] Enable new connection

        # DROP NEW CLIENT - QUEUE FULL!
        Client.console("------- connection busy")
        await new_client.a_send("Connection is busy. Bye!")
        await new_client.close()    # Play nicely - close connection
        del new_client              # Clean up unused client
        return False                        # [!] Deny new client

    async def shell_cli(self, reader, writer):
        """
        Handle incoming new async requests towards the server
        - creates ShellCli object with the new incoming connection
        - Client implements micrOS shell interface over reader, sender tcp connection
        """
        # Create ShellCli instance
        new_client = ShellCli(reader, writer)
        # Accept incoming client with queue limit check
        if not await self.accept_client(new_client):
            # Server busy - skip connection (accept_client auto-close feature)
            return
        # Run new_client shell prompt
        await new_client.run_shell()

    async def web_cli(self, reader, writer):
        """
        Handle incoming new async requests towards the server
        - creates WebCli object with the new incoming connection
        - WebCli handles simple http get requests over tcp connection
        """
        # Create WebCli instance
        new_client = WebCli(reader, writer)
        # Accept incoming client with queue limit check
        if not await self.accept_client(new_client):
            # Server busy - skip connection (accept_client auto-close feature)
            return
        # Run new_client web (http) cli
        await new_client.run_web()

    async def run_server(self):
        """
        Define async socket server (tcp by default)
        """
        addr = ifconfig()[1][0]
        Client.console(f"[ socket server ] Start socket server on {addr}")
        self.server = asyncio.start_server(self.shell_cli, self._host, self._port, backlog=self._socqueue)
        await self.server
        Client.console(f"- TCP server ready, connect: telnet {addr} {self._port}")
        if cfgget('webui'):
            self.web = asyncio.start_server(self.web_cli, self._host, 80, backlog=self._socqueue)
            await self.web
            Client.console(f"- HTTP server ready, connect: http://{addr}")

    @staticmethod
    def reply_all(msg):
        """
        Reply All - stream data to all connection...
        Only used for LM msg stream over Common.socket_stream wrapper
        """
        for _, cli in Client.ACTIVE_CLIS.items():
            if cli.connected:
                cli.send(msg)

    def __del__(self):
        Client.console("[ socket server ] <<destructor>>")
        self.server.close()
