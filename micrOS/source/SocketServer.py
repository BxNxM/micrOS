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

# from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
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
        if Debug.INDENT < 50:
            # if less then max indent
            Debug.INDENT += 1


#########################################################
#          SOCKET SERVER-CLIENT HANDLER CLASS           #
#########################################################

class Client:
    TASK_MANAGER = Manager()

    def __init__(self, reader, writer):
        self.connected = True
        self.reader = reader
        self.writer = writer
        self.drain_event = asyncio.Event()
        self.drain_event.set()

        self.client_id = writer.get_extra_info('peername')
        self.shell = Shell(self.send)
        self.last_msg_t = ticks_ms()
        Debug().console("[Client] new conn: {}".format(self.client_id))

    async def read(self):
        """
        Implements client read function
        - set timeout counter
        - read input from client (run: return False)
        - connection error handling (stop: return True)
        - exit command handling (stop: return True)
        """
        Debug().console("[Client] read {}".format(self.client_id))
        self.last_msg_t = ticks_ms()
        try:
            request = (await self.reader.read(2048))
            request = request.decode('utf8').strip()
        except Exception as e:
            Debug().console("[Client] Stream read error ({}): {}".format(self.client_id, e))
            return True, ''

        # Input handling
        Debug().console("[Client] raw request ({}): |{}|".format(self.client_id, request))
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
                response = "{}\n".format(response)
            #Debug().console("[Client] ----- SteamWrite: {}".format(response))
            # Store data in stream buffer
            self.writer.write(response.encode('utf8'))
            # Send buffered data with async task - hacky
            Client.TASK_MANAGER.loop.create_task(self.__wait_for_drain())
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
            #Debug().console("  |----- start drain")
            await self.writer.drain()
            #Debug().console("  |------ stop drain")
        except Exception as e:
            Debug().console("[Client] Drain error -> close conn: {}".format(e))
            await self.close()
        # set drain free
        self.drain_event.set()

    async def close(self):
        Debug().console("[Client] Close connection {}".format(self.client_id))
        # Reset shell state machine
        self.shell.reset()
        self.send("Bye!\n")
        await asyncio.sleep_ms(100)
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception as e:
            Debug().console("[Client] Close error: {}".format(e))
        self.connected = False
        Debug.INDENT = 0

    async def shell_cmd(self, request):
        # Run micrOS shell with request string
        try:
            Debug().console("[CLIENT] --- #Run shell")
            state = self.shell.shell(request)
            if state:
                return True
        except Exception as e:
            if "ECONNRESET" in e:
                await self.close()
            Debug().console("[Client] Shell exception: {}".format(e))
            return False
        collect()
        self.send("[HA] Shells cleanup: {}".format(mem_free()))
        return True

    def __del__(self):
        Debug().console("Delete client connection: {}".format(self.client_id))


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
            SocketServer.__instance.server_console_indent = 0
            SocketServer.__instance.client = None

            # ---- Config ---
            SocketServer.__instance.__port = cfgget("socport")
            # ---- Set socket timeout (min 5 sec!!! hardcoded)
            soc_timeout = int(cfgget("soctout"))
            SocketServer.__instance.soc_timeout = 5 if soc_timeout < 5 else soc_timeout
            # ---         ----
            Debug().console("[ socket server ] <<constructor>>")
        return SocketServer.__instance

    #####################################
    #       Socket Server Methods       #
    #####################################

    async def accept_client(cls, new_client):
        # Get new client ID
        client_id = new_client.client_id
        # Check there is open connection
        if cls.client is None:
            return True, client_id

        # Get active client timeout counter
        client_inactive = int(ticks_diff(ticks_ms(), cls.client.last_msg_t) * 0.001)
        Debug().console("[server] accept client {} - isconn: {}({}):{}s".format(client_id, cls.client.connected,
                                                                          cls.client.client_id, cls.soc_timeout-client_inactive))
        if cls.client.connected:
            if client_inactive < cls.soc_timeout:
                # THERE IS ACTIVE OPEN CONNECTION, DROP NEW CLIENT!
                Debug().console("------- connection busy")
                # Handle only single connection
                new_client.send("Connection is busy. Bye!")
                await new_client.close()    # Play nicely - close connection
                del new_client              # Clean up unused client
                return False, client_id
            else:
                # OPEN CONNECTION IS INACTIVE > CLOSE
                Debug().console("------- connection - client timeout - accept new connection")
                await cls.client.close()
        return True, client_id

    async def handle_client(cls, reader, writer):
        """
        Handle async requests towards server
        """
        # Create client object
        new_client = Client(reader, writer)

        # Check incoming client
        state, client_id = await cls.accept_client(new_client)
        if not state:
            # Server busy, there is one active open connection - reject client
            # delete unused new_client as well!
            return

        # Store client object as active client
        cls.client = new_client

        # Init prompt
        cls.client.send(cls.client.shell.prompt())
        # Run async connection handling
        while cls.client.connected:
            try:
                # Read request msg from client
                state, request = await cls.client.read()
                if state:
                    break

                state = await cls.client.shell_cmd(request)
                if not state:
                    cls.client.send("[HA] Critical error - disconnect & hard reset")
                    errlog_add("[ERR] Socket critical error - reboot")
                    cls.client.shell.reboot()
            except Exception as e:
                errlog_add("[ERR] handle_client: {}".format(e))
                break
        # Close connection
        await cls.client.close()

    async def run_server(cls):
        """
        Define async socket server (tcp by default)
        """
        addr = ifconfig()[1][0]
        Debug().console("[ socket server ] Start socket server on {}:{}".format(addr, cls.__port))
        Debug().console("- connect: telnet {} {}".format(addr, cls.__port))
        cls.server = asyncio.start_server(cls.handle_client, cls.__host, cls.__port, backlog=1)
        await cls.server
        Debug().console("-- TCP server running in background")

    def reply_message(cls, msg):
        """
        Only used for LM msg stream over Common.socket_stream wrapper
        - single connection support!!!
        """
        if cls.client is None:
            return
        cls.client.send(msg)

    def __del__(cls):
        Debug().console("[ socket server ] <<destructor>>")
        cls.server.close()
