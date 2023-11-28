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

from ConfigHandler import cfgget
from Debug import console_write, errlog_add
from Shell import Shell
from Network import ifconfig
import uasyncio as asyncio
from TaskManager import Manager
from utime import ticks_ms, ticks_diff
try:
    from gc import collect, mem_free
except:
    console_write("[SIMULATOR MODE GC IMPORT]")
    from simgc import collect, mem_free


class Debug:
    INDENT = 0

    @staticmethod
    def console(msg):
        console_write("|" + "-" * Debug.INDENT + msg)
        Debug.INDENT += 1 if Debug.INDENT < 50 else 0       # Auto indent


#########################################################
#         SOCKET SERVER-CLIENT HANDLER CLASSES          #
#           Client (Base), ShellCli, WebCli             #
#########################################################

class Client:
    ACTIVE_CLIS = {}

    def __init__(self, reader, writer):
        self.connected = True
        self.reader = reader
        self.writer = writer
        # Set client ID - TODO: set prefix by child type (ShellCli or WebCli)
        client_id = writer.get_extra_info('peername')
        self.client_id = f"{'.'.join(client_id[0].split('.')[-2:])}:{str(client_id[1])}"
        self.last_msg_t = ticks_ms()

    async def read(self):
        """
        [Base] Implements client read function, reader size: 2048
        - set timeout counter
        - read input from client (run: return False)
        - connection error handling (stop: return True)
        - exit command handling (stop: return True)
        """
        Debug.console(f"[Client] read {self.client_id}")
        self.last_msg_t = ticks_ms()
        try:
            request = (await self.reader.read(2048))
            request = request.decode('utf8').strip()
        except Exception as e:
            Debug.console(f"[Client] Stream read error ({self.client_id}): {e}")
            collect()           # gc collection: "fix" for memory allocation failed, allocating 2049 bytes
            return True, ''

        # Input handling
        Debug.console(f"[Client] raw request ({self.client_id}): |{request}|")
        if request in ('exit', ''):
            return True, request
        return False, request

    async def a_send(self, response):
        """
        [Base] Async socket send method
        """
        if self.connected:
            # Debug.console("[Client] ----- SteamWrite: {}".format(response))
            # Store data in stream buffer
            try:
                self.writer.write(response.encode('utf8'))
            except Exception as e:
                # Maintain ACTIVE_CLIS - remove closed connection by peer.
                await self.close()
                errlog_add(f"[WARN] Client.a_send (auto-drop) {self.client_id}: {e}")
            # Send buffered data with async task - hacky
            try:
                # send write buffer
                # Debug.console("  |----- start drain")
                await self.writer.drain()
                # Debug.console("  |------ stop drain")
            except Exception as e:
                Debug.console(f"[Client] Drain error -> close conn: {e}")
                await self.close()
        else:
            console_write(f"[Client] NoCon: {response}")

    def send(self, response):
        # Implement in child class
        pass

    async def close(self):
        """
        [Base] Async socket close method
        """
        Debug.console(f"[Client] Close connection {self.client_id}")
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception as e:
            Debug.console(f"[Client] Close error {self.client_id}: {e}")
        self.connected = False
        Debug.INDENT = 0
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
        Manager().server_task_msg(','.join(list(Client.ACTIVE_CLIS.keys())))

    def __del__(self):
        """Client GC collect"""
        collect()
        Debug.console(f"[Client] del: {self.client_id}")


class WebCli(Client):

    def __init__(self, reader, writer):
        Client.__init__(self, reader, writer)

    async def response(self, request):
        """HTTP GET REQUEST WITH /WEB - SWITCH TO WEB INTERFACE"""
        Debug.console("[WebCli] --- HTTP REQUEST DETECTED")
        if request.startswith('GET /rest'):
            Debug.console("[WebCli] --- /REST accept")      # REST API (GET)
            try:
                await self.a_send(self.rest(request))
            except Exception as e:
                response = f"HTTP/1.1 404 {e}\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\n404 Not Found"
                await self.a_send(response)
            return

        if request.startswith('GET /'):
            Debug.console("[WebCli] --- / accept")          # HOMEPAGE ENDPOINT (fallback as well)
            try:
                with open('index.html', 'r') as file:
                    html = file.read()
                response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length:{len(html)}\r\n\r\n{html}"
            except OSError:
                response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 13\r\n\r\n404 Not Found"
            await self.a_send(response)
            return

        # Neither GET / or /rest request - handle error message
        response = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/plain\r\nContent-Length: 15\r\n\r\n400 Bad Request"
        await self.a_send(response)

    async def run_web(self):
        # Update server task output (? test ?)
        Manager().server_task_msg(','.join(list(Client.ACTIVE_CLIS.keys())))

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

    def rest(self, request):
        resp_schema = {'result': None, 'state': False}
        cmd = request.split()[1].replace('/rest', '')
        if len(cmd) > 1:
            # REST sub-parameter handling (rest commands)
            cmd = cmd.replace('/', ' ').strip()
            # TODO: call LM
            resp_schema['result'] = f"Exec: {cmd}"
            resp_schema['state'] = True
        else:
            resp_schema['result'] = f"Homepage"
            resp_schema['state'] = True
        response = f"'{resp_schema}'"
        return f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length:{len(response)}\r\n\r\n{response}"


class ShellCli(Client, Shell):

    def __init__(self, reader, writer):
        Client.__init__(self, reader, writer)
        Debug.console(f"[ShellCli] new conn: {self.client_id}")
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
            # Debug.console("[Client] ----- SteamWrite: {}".format(response))
            # Store data in stream buffer
            try:
                self.writer.write(response.encode('utf8'))
            except Exception as e:
                # Maintain ACTIVE_CLIS - remove closed connection by peer.
                Client.drop_client(self.client_id)
                errlog_add(f"[WARN] ShellCli.send (auto-drop) {self.client_id}: {e}")
            # Send buffered data with async task - hacky
            asyncio.get_event_loop().create_task(self.__wait_for_drain())
        else:
            console_write(f"[ShellCli] NoCon: {response}")

    async def __wait_for_drain(self):
        """
        Handle drain serialization
        - solve output data duplicate
        """
        # Wait for event set (True) - drain is free
        await self.drain_event.wait()

        # set drain busy
        self.drain_event.clear()
        try:
            # send write buffer
            # Debug.console("  |----- start drain")
            await self.writer.drain()
            # Debug.console("  |------ stop drain")
        except Exception as e:
            Debug.console(f"[ShellCli] Drain error -> close conn: {e}")
            await self.close()
        # set drain free
        self.drain_event.set()

    async def close(self):
        Debug.console(f"[ShellCli] Close connection {self.client_id}")
        self.send("Bye!\n")
        # Reset shell state machine
        self.reset()
        await asyncio.sleep_ms(50)
        # Used from Client parent class
        await super().close()

    async def __shell_cmd(self, request):
        """
        Handle micrOS shell and /web http endpoints
        """
        # Run micrOS shell with request string
        try:
            # Handle micrOS shell
            Debug.console("[ShellCli] --- #Run shell")
            state = self.shell(request)
            if state:
                return True
        except Exception as e:
            if "ECONNRESET" in str(e):
                await self.close()
            Debug.console(f"[ShellCli] Shell exception: {e}")
            return False
        collect()
        self.send(f"[HA] Shells cleanup: {mem_free()}")
        return True

    async def run_shell(self):
        # Update server task output (? test ?)
        Manager().server_task_msg(','.join(list(Client.ACTIVE_CLIS.keys())))

        # Init prompt
        self.send(self.prompt())
        # Run async connection handling
        while self.connected:
            try:
                # Read request msg from client
                state, request = await self.read()
                if state:
                    break

                state = await self.__shell_cmd(request)
                if not state:
                    self.send("[HA] Critical error - disconnect & hard reset")
                    errlog_add("[ERR] Socket critical error - reboot")
                    self.reboot()
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
            self.server = None
            self._host = ''
            self._conn_queue = 2            # CONNECTION QUEUE SIZE, common for both interface

            # ---- Config ---
            self._port = cfgget("socport")
            # ---- Set socket timeout (min 5 sec!!! hardcoded)
            soc_timeout = int(cfgget("soctout"))
            self._timeout = 5 if soc_timeout < 5 else soc_timeout
            # ---         ----
            self._initialized = True
            Debug.console("[ socket server ] <<constructor>>")

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
        if len(list(Client.ACTIVE_CLIS.keys())) < self._conn_queue:
            # Add new client to active clients dict
            Client.ACTIVE_CLIS[new_client_id] = new_client
            return True, new_client_id      # [!] Enable new connection

        # Get active clients timeout counters - handle new client depending on active client timeouts
        Debug.console(f"NEW CLIENT CONN: {new_client_id}")
        enable_new = False
        for cli_id, cli in Client.ACTIVE_CLIS.items():
            cli_inactive = int(ticks_diff(ticks_ms(), cli.last_msg_t) * 0.001)
            Debug.console(f"[server] accept new {new_client_id} - active {cli_id} tout:{self._timeout - cli_inactive}s")
            if not cli.connected or cli_inactive > self._timeout:
                # OPEN CONNECTION IS INACTIVE > CLOSE
                Debug.console("------- client timeout - accept new connection")
                await cli.close()
                enable_new = True
                break

        # Interpret new connection is possible ...
        if enable_new:
            return True, new_client_id  # [!] Enable new connection
        # THERE IS ACTIVE OPEN CONNECTION, DROP NEW CLIENT!
        Debug.console("------- connection busy")
        # Handle only single connection
        await new_client.a_send("Connection is busy. Bye!")
        await new_client.close()  # Play nicely - close connection
        del new_client  # Clean up unused client
        return False, new_client_id     # [!] Deny new client

    async def shell_cli(self, reader, writer):
        """
        Handle incoming new async requests towards the server
        - creates ShellCli object with the new incoming connection
        - Client implements micrOS shell interface over reader, sender tcp connection
        """
        # Create client object
        new_client = ShellCli(reader, writer)

        # Check incoming client - client queue limitation
        state, client_id = await self.accept_client(new_client)
        if not state:
            # Server busy, there is one active open connection - reject client
            # close unused new_client as well!
            return

        # Store client object as active client
        await new_client.run_shell()

    async def web_cli(self, reader, writer):
        """
        Handle incoming new async requests towards the server
        - creates WebCli object with the new incoming connection
        - WebCli handles simple http get requests over tcp connection
        """
        # Create client object
        new_client = WebCli(reader, writer)

        # Check incoming client - client queue limitation
        state, client_id = await self.accept_client(new_client)
        if not state:
            # Server busy, there is one active open connection - reject client
            # close unused new_client as well!
            return

        # Run web (http) cli
        await new_client.run_web()

    async def run_server(self):
        """
        Define async socket server (tcp by default)
        """
        addr = ifconfig()[1][0]
        Debug.console(f"[ socket server ] Start socket server on {addr}:{self._port}")
        self.server = asyncio.start_server(self.shell_cli, self._host, self._port, backlog=self._conn_queue)
        await self.server
        if cfgget('webui'):
            web = asyncio.start_server(self.web_cli, self._host, 80, backlog=self._conn_queue)
            await web
        Debug.console(f"- TCP server ready, connect: telnet {addr} {self._port}")

    @staticmethod
    def reply(msg):
        """
        Only used for LM msg stream over Common.socket_stream wrapper
        - stream data to all connection...
        """
        for cli_id, cli in Client.ACTIVE_CLIS.items():
            if cli.connected:
                cli.send(msg)

    def __del__(self):
        Debug.console("[ socket server ] <<destructor>>")
        self.server.close()
