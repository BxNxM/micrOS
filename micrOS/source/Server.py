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
from Buffer import SlidingBuffer, BufferFullError, MemoryPool
from Config import cfgget
from Debug import console_write, syslog
from Network import ifconfig
from Tasks import Manager
from Shell import Shell
try:
    from gc import collect, mem_free
except:
    console_write("[SIMULATOR MODE GC IMPORT]")
    from simgc import collect, mem_free

# Module load optimization, needed only for webui
if cfgget('webui'):
    from Web import WebEngine
else:
    # Create dummy web engine - Lazy loading
    class WebEngine:
        __slots__ = []
        def __init__(self, *args, **kwargs):
            pass
        @staticmethod
        def register(*args, **kwargs) -> None:
            """Child class can implement"""
            syslog(f"[WARN] webui disabled, skip register: {kwargs.get('endpoint')}")
        @staticmethod
        def web_mounts(*args, **kwargs) -> dict:
            """Child class can implement"""
            syslog(f"[WARN] webui disabled, skip web_mounts: {kwargs.get('endpoint')}")
            return {}

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

    async def read(self, decoding='utf8', timeout_seconds=0, read_bytes = None):
        """
        [Base] Implements client read function
        :return tuple: read_error, data
        - read_error is set to true upon timeout or other exception
        - data holds bytes or decoded string read from the socket
        """
        Client.console(f"[Client] read {self.client_id}")
        self.last_msg_t = ticks_ms()
        num_bytes = read_bytes or self.read_bytes
        try:
            if timeout_seconds:
                request = await asyncio.wait_for(self.reader.read(num_bytes), timeout_seconds)
            else:
                request = await self.reader.read(num_bytes)
            if decoding:
                request = request.decode(decoding)
        except asyncio.TimeoutError:
            Client.console(f"[Client] Stream read timeout ({self.client_id}), timeout={timeout_seconds}s")
            return False, ''
        except Exception as e:
            Client.console(f"[Client] Stream read error ({self.client_id}): {e}")
            collect()           # gc collection: "fix" for memory allocation failed, allocating 2049 bytes
            return True, ''

        # Input handling
        Client.console(f"[Client] raw request ({self.client_id}): |{request}|")
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
                syslog(f"[WARN] Client.a_send (auto-drop) {self.client_id}: {e}")
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
        # Optional - Implement in child class - synchronous send (all) method
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
        Client.console(f"[Client] {client_id} dropped")
        if Client.ACTIVE_CLIS.get(client_id, None) is not None:
            Client.ACTIVE_CLIS.pop(client_id)
        # Update server task output (? test ?)
        Manager().task_msg('server', ','.join(list(Client.ACTIVE_CLIS)))

    def __del__(self):
        """Client GC collect"""
        collect()
        Client.console(f"[Client] del: {self.client_id}")


class WebCli(Client):
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
        usable = int(WebCli.MEM_CAP * mem_available)
        is_low_memory = (usable / con_limit) < \
            (WebCli.RECV_BUF_MAX_BYTES + WebCli.SEND_BUF_MAX_BYTES + WebCli.CONN_OVERHEAD)
        if is_low_memory:
            syslog((
                "[INFO] Webcli.init_pools: low-memory mode with reduced buffer size, "
                "decrease webui_max_con to use larger buffers"
            ))
        recv_size = WebCli.RECV_BUF_MIN_BYTES if is_low_memory else WebCli.RECV_BUF_MAX_BYTES
        send_size = WebCli.SEND_BUF_MIN_BYTES if is_low_memory else WebCli.SEND_BUF_MAX_BYTES
        per_conn = recv_size + send_size + WebCli.CONN_OVERHEAD
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
        WebCli.RECV_POOL = MemoryPool(recv_size, con_limit, wrapper=SlidingBuffer)
        WebCli.SEND_POOL = MemoryPool(send_size, con_limit, wrapper=SlidingBuffer)

    __slots__ = (
        "_engine",
        "_prev_state",
        "_recv_buf",
        "_send_buf"
    )

    def __init__(self, reader, writer):
        super().__init__(reader, writer, r_size=WebCli.MTU_SIZE)
        self._engine = WebEngine(version=Shell.MICROS_VERSION)
        self._prev_state = None
        self._recv_buf = None
        self._send_buf = None

    async def _flush_response(self):
        data = self._send_buf.peek()
        for i in range(0,len(data),WebCli.MTU_SIZE):
            self.writer.write(data[i:i+WebCli.MTU_SIZE])
            await self.writer.drain()
        self._send_buf.consume()

    async def run_web(self):
        Manager().task_msg('server', ','.join(list(Client.ACTIVE_CLIS)))
        await self._reserve_buffers()
        self._prev_state = None
        try:
            while self._engine.state is not None:
                await self._run_state_machine()
                await asyncio.sleep_ms(WebCli.STATE_MACHINE_SLEEP_MS)
        except Exception as e:
            syslog(f"[ERR] run_web: {e}")
        finally:
            if self._send_buf:
                self._send_buf.consume()
                WebCli.SEND_POOL.release(self._send_buf)
            if self._recv_buf:
                self._recv_buf.consume()
                WebCli.RECV_POOL.release(self._recv_buf)
            await self.close()
            collect()

    async def _reserve_buffers(self):
        if WebCli.SEND_POOL is None or WebCli.RECV_POOL is None:
            raise RuntimeError("Buffer pools are uninitialized")

        while not self._recv_buf or not self._send_buf:
            if not self._recv_buf:
                self._recv_buf = WebCli.RECV_POOL.reserve()
            if not self._send_buf:
                self._send_buf = WebCli.SEND_POOL.reserve()
            await asyncio.sleep_ms(WebCli.STATE_MACHINE_SLEEP_MS)

    async def _run_state_machine(self):
        if self._prev_state == self._engine.state or self._prev_state is None:
            num_read = await self._read_to_buf()
            if not num_read:
                return
        try:
            resp_handler = None
            while self._engine.state is not None:
                self._prev_state = self._engine.state
                resp_handler = self._engine.state(self._recv_buf, self._send_buf)
                if not self._send_buf.size():
                    break
                await self._flush_response()
                await asyncio.sleep_ms(WebCli.STATE_MACHINE_SLEEP_MS)
        except BufferFullError:
            self._engine.on_failure(self._send_buf, b'Buffer full')
            await self._flush_response()
            return
        except Exception as e:
            syslog(f"[ERR] run_web: {e}")
            self._engine.on_failure(self._send_buf, str(e).encode("ascii"))
            await self._flush_response()
            return
        if self._engine.state is None and resp_handler is not None:
            await self._response_handler(resp_handler)

    async def _read_to_buf(self):
        buf_free = self._recv_buf.capacity - self._recv_buf.size()
        if not buf_free:
            self._engine.on_buffer_full(self._send_buf)
            await self._flush_response()
            return 0
        error, request = await self.read(decoding=None,
                                         timeout_seconds=WebCli.RECV_TIMEOUT_SECONDS,
                                         read_bytes=buf_free)
        if error:
            self._engine.on_failure(self._send_buf, b"Read error")
            await self._flush_response()
            return 0
        if not request:
            self._engine.on_timeout(self._send_buf)
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
                await asyncio.sleep_ms(WebCli.RESP_HANDLER_SLEEP_MS)
        #elif type(resp_handler).__name__ in ("FileIO", "BytesIO"):     # NOT WORKS ON SIMULATOR
        elif hasattr(resp_handler, "readinto"):
            with resp_handler as rh:
                while True:
                    view = self._send_buf.writable_view()
                    num_read = rh.readinto(view)
                    if not num_read:
                        break
                    self._send_buf.commit(num_read)
                    await self._flush_response()
                    await asyncio.sleep_ms(WebCli.RESP_HANDLER_SLEEP_MS)
        else:
            self._engine.on_failure(self._send_buf, f"Invalid response handler {type(resp_handler).__name__}".encode("ascii"))
            await self._flush_response()


class ShellCli(Client, Shell):
    def __init__(self, reader, writer):
        Client.__init__(self, reader, writer, r_size=2048)          # r_size: 2048 default on ShellCli!
        Client.console(f"[ShellCli] new conn: {self.client_id}")
        self.drain_event = asyncio.Event()
        self.drain_event.set()
        Shell.__init__(self)

    def send(self, response):
        """
        Synchronous send function (with drain task)
        - not used in Shell or ShellCli
        - Note: it is a support function for synchronous scenarios: Server.reply_all
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
                syslog(f"[WARN] ShellCli.send (auto-drop) {self.client_id}")
            # Send buffered data with async task - hacky
            if self.drain_event.is_set():
                self.drain_event.clear()        # set drain busy (False)
                asyncio.get_event_loop().create_task(self.__wait_for_drain())
        else:
            console_write("[ShellCli] NoCon: response>/dev/nul")

    async def __wait_for_drain(self):
        """
        Handle drain serialization - for synchronous send function
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

    async def a_send(self, response, encode='utf8'):
        """
        Async send for Shell (new line + prompt$)
        """
        if self.prompt() != response:
            # [format] Add new line if not prompt
            response = f"{response}\n"
        await super().a_send(response, encode)

    async def run_shell(self):
        # Update server task output
        Manager().task_msg('server', ','.join(list(Client.ACTIVE_CLIS)))
        # Init prompt
        await self.a_send(self.prompt())
        # Run async connection handling
        _exit = False
        while self.connected:
            try:
                # Read request msg from client
                state, request = await self.read()
                if state or request in ('exit', ''):
                    break
                # Run micrOS shell with request string
                Client.console("[ShellCli] --- #Run shell")
                # Shell -> True (OK) or False (NOK) -> NOK->Close session (auth Failed, etc.)
                _exit = not await self.shell(request)
            except Exception as e:
                syslog(f"[ERR] Shell client: {e}")
                if "ECONNRESET" in str(e):
                    _exit = True  # exit_loop
                else:
                    await self.a_send("[HA] Critical error - disconnect & hard reset")
                    syslog("[ERR] Socket critical error - reboot")
                    await self.reboot()
            if _exit:
                collect()
                break
        # Close connection
        await self.a_send("Bye!")
        await self.close()


#########################################################
#                    SOCKET SERVER CLASS                #
#########################################################

class Server:
    """
    Socket message data packet layer - send and receive
    Embedded command interpretation:
    - exit
    Handle user requests/commands with Shell (bash like experience)
    """
    __slots__ = ['server', 'web', '_host', '_socqueue', '_port', '_timeout', '_initialized']
    __instance = None

    CON_ACCEPT_TIMEOUT_MS = 5000 # Timeout value for accepting new connection
    CON_ACCEPT_SLEEP_MS = 100    # Duration of sleep between attempts to accept new connection

    def __new__(cls):
        """
        Singleton design pattern
        __new__ - Customize the instance creation
        cls     - class
        """
        if not cls.__instance:
            # Server singleton properties
            cls.__instance = super(Server, cls).__new__(cls)
            cls.__instance._initialized = False
        return cls.__instance

    def __init__(self):
        if not self._initialized:
            # Socket server initial parameters
            self.server = None                                  # ShellCli server instance
            self.web = None                                     # WebCli server instance
            self._host = '0.0.0.0'                              # listens on all available interfaces
            self._socqueue = max(1, int(cfgget("aioqueue")))    # CONNECTION QUEUE SIZE, common for both interface

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

        # Get active clients timeout counters - handle new client depending on active client timeouts
        Client.console(f"NEW CLIENT CONN: {new_client_id}")
        con_timestamp = ticks_ms()
        while ticks_ms() - con_timestamp < Server.CON_ACCEPT_TIMEOUT_MS:
            # Add new client immediately if queue not full
            if len(list(Client.ACTIVE_CLIS.keys())) < self._socqueue:
                # Add new client to active clients dict
                Client.ACTIVE_CLIS[new_client_id] = new_client
                return True                     # [!] Enable new connection
            # Attempt to evict inactive clients
            for cli_id, cli in Client.ACTIVE_CLIS.items():
                cli_inactive = int(ticks_diff(ticks_ms(), cli.last_msg_t) * 0.001)
                Client.console(f"[server] accept new {new_client_id} - active {cli_id} tout:{self._timeout - cli_inactive}s")
                if not cli.connected or cli_inactive > self._timeout:
                    # OPEN CONNECTION IS INACTIVE > CLOSE
                    Client.console("------- client timeout - accept new connection")
                    await cli.close()
                    return True                 # [!] Enable new connection
            await asyncio.sleep_ms(Server.CON_ACCEPT_SLEEP_MS)

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
            try:
                collect()
                WebCli.init_pools()
                self.web = asyncio.start_server(self.web_cli, self._host, 80, backlog=self._socqueue)
                await self.web
                Client.console(f"- HTTP server ready, connect: http://{addr}")
            except MemoryError as e:
                Client.console(f"- HTTP server memory error: {self.client_id}: {e}")

    @staticmethod
    def reply_all(msg):
        """
        Reply All - stream data to all connection...
        Only used for LM msg stream over Common.socket_stream wrapper
        """
        for _, cli in Client.ACTIVE_CLIS.items():
            if cli.connected:
                cli.send(f"~~~ {msg}")

    def __del__(self):
        Client.console("[ socket server ] <<destructor>>")
        if self.server:
            self.server.close()
        if self.web:
            self.web.close()
