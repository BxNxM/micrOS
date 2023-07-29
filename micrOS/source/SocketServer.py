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
from InterpreterShell import Shell
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
#          SOCKET SERVER-CLIENT HANDLER CLASS           #
#########################################################

class Client:
    ACTIVE_CLIS = {}

    def __init__(self, reader, writer):
        self.connected = True
        self.reader = reader
        self.writer = writer
        self.drain_event = asyncio.Event()
        self.drain_event.set()

        self.client_id = writer.get_extra_info('peername')
        Debug.console(f"[Client] new conn: {self.client_id}")
        client_tag = f"{'.'.join(self.client_id[0].split('.')[-2:])}:{str(self.client_id[1])}"
        self.client_id = client_tag
        self.shell = Shell(self.send)
        self.last_msg_t = ticks_ms()

    async def read(self):
        """
        Implements client read function, reader size: 2048
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
        if request == 'exit' or request == '':
            return True, request
        return False, request

    def send(self, response):
        """
        Send response to client with non-async function
        """
        if self.connected:
            if self.shell.prompt() != response:
                # Add new line if not prompt (?)
                response = f"{response}\n"
            # Debug.console("[Client] ----- SteamWrite: {}".format(response))
            # Store data in stream buffer
            try:
                self.writer.write(response.encode('utf8'))
            except Exception as e:
                # Maintain ACTIVE_CLIS - remove closed connection by peer.
                Client.drop_client(self.client_id)
                errlog_add(f"[WARN] Client.send (auto-drop) {self.client_id}: {e}")
            # Send buffered data with async task - hacky
            asyncio.get_event_loop().create_task(self.__wait_for_drain())
        else:
            print(response)

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
            Debug.console(f"[Client] Drain error -> close conn: {e}")
            await self.close()
        # set drain free
        self.drain_event.set()

    async def close(self):
        Debug.console(f"[Client] Close connection {self.client_id}")
        self.send("Bye!\n")
        # Reset shell state machine
        self.shell.reset()
        await asyncio.sleep_ms(50)
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
        if Client.ACTIVE_CLIS.get(client_id, None) is not None:
            Client.ACTIVE_CLIS.pop(client_id)
        # Update server task output (? test ?)
        Manager().server_task_msg(','.join(list(Client.ACTIVE_CLIS.keys())))

    async def __shell_cmd(self, request):
        # Run micrOS shell with request string
        try:
            Debug.console("[CLIENT] --- #Run shell")
            state = self.shell.shell(request)
            if state:
                return True
        except Exception as e:
            if "ECONNRESET" in e:
                await self.close()
            Debug.console(f"[Client] Shell exception: {e}")
            return False
        collect()
        self.send(f"[HA] Shells cleanup: {mem_free()}")
        return True

    async def run_shell(self):
        # Update server task output (? test ?)
        Manager().server_task_msg(','.join(list(Client.ACTIVE_CLIS.keys())))

        # Init prompt
        self.send(self.shell.prompt())
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
                    self.shell.reboot()
            except Exception as e:
                errlog_add(f"[ERR] handle_client: {e}")
                break
        # Close connection
        await self.close()

    def __del__(self):
        collect()
        Debug.console(f"Delete client connection: {self.client_id}")


#########################################################
#                    SOCKET SERVER CLASS                #
#########################################################

class SocketServer:
    """
    Socket message data packet layer - send and receive
    Embedded command interpretation:
    - exit
    - reboot
    InterpreterShell invocation with msg data
    """
    __instance = None

    def __new__(cls):
        """
        Singleton design pattern
        __new__ - Customize the instance creation
        cls     - class
        """
        if SocketServer.__instance is None:
            # SocketServer singleton properties
            SocketServer.__instance = super().__new__(cls)
            # Socket server initial parameters
            SocketServer.__instance.__host = ''
            SocketServer.__instance.server = None
            SocketServer.__instance.__conn_queue = 2

            # ---- Config ---
            SocketServer.__instance.__port = cfgget("socport")
            # ---- Set socket timeout (min 5 sec!!! hardcoded)
            soc_timeout = int(cfgget("soctout"))
            SocketServer.__instance.soc_timeout = 5 if soc_timeout < 5 else soc_timeout
            # ---         ----
            Debug.console("[ socket server ] <<constructor>>")
        return SocketServer.__instance

    #####################################
    #       Socket Server Methods       #
    #####################################

    async def accept_client(cls, new_client):
        """
        Client handler
        - check active connection timeouts
        - accept new if fits in queue
        :param new_client: new Client class object
        """
        # Get new client ID
        new_client_id = new_client.client_id

        # Add new client immediately if queue not full
        if len(list(Client.ACTIVE_CLIS.keys())) < cls.__conn_queue:
            # Add new client to active clients dict
            Client.ACTIVE_CLIS[new_client_id] = new_client
            return True, new_client_id      # [!] Enable new connection

        # Get active clients timeout counters - handle new client depending on active client timeouts
        Debug.console(f"NEW CLIENT CONN: {new_client_id}")
        enable_new = False
        for cli_id, cli in Client.ACTIVE_CLIS.items():
            cli_inactive = int(ticks_diff(ticks_ms(), cli.last_msg_t) * 0.001)
            Debug.console(f"[server] accept new {new_client_id} - active {cli_id} tout:{cls.soc_timeout - cli_inactive}s")
            if not cli.connected or cli_inactive > cls.soc_timeout:
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
        new_client.send("Connection is busy. Bye!")
        await new_client.close()  # Play nicely - close connection
        del new_client  # Clean up unused client
        return False, new_client_id     # [!] Deny new client

    async def handle_client(cls, reader, writer):
        """
        Handle incoming new async requests towards the server
        - creates Client object with the new incoming connection
        - Client implements micrOS shell interface over reader, sender tcp connection
        """
        # Create client object
        new_client = Client(reader, writer)

        # Check incoming client - client queue limitation
        state, client_id = await cls.accept_client(new_client)
        if not state:
            # Server busy, there is one active open connection - reject client
            # close unused new_client as well!
            return

        # Store client object as active client
        await new_client.run_shell()

    async def run_server(cls):
        """
        Define async socket server (tcp by default)
        """
        addr = ifconfig()[1][0]
        Debug.console(f"[ socket server ] Start socket server on {addr}:{cls.__port}")
        cls.server = asyncio.start_server(cls.handle_client, cls.__host, cls.__port, backlog=cls.__conn_queue)
        await cls.server
        Debug.console(f"- TCP server ready, connect: telnet {addr} {cls.__port}")

    @staticmethod
    def reply(msg):
        """
        Only used for LM msg stream over Common.socket_stream wrapper
        - stream data to all connection...
        """
        for cli_id, cli in Client.ACTIVE_CLIS.items():
            if cli.connected:
                cli.send(msg)

    def __del__(cls):
        Debug.console("[ socket server ] <<destructor>>")
        cls.server.close()
