"""
Module is responsible for socket server
dedicated to micrOS framework.
- The heart of communication
- micrOS version handler
- Maintain connections
- built in exposed commands
    - hello
    - version
    - exit
    - reboot
- server recovery handling
- providing server console instance

Designed by Marcell Ban aka BxNxM
"""
#########################################################
#                         IMPORTS                       #
#########################################################

from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from time import sleep
from ConfigHandler import console_write, cfgget, cfgput
from InterpreterShell import shell as InterpreterShell_shell

try:
    from gc import collect, mem_free
except:
    console_write("[SIMULATOR MODE GC IMPORT]")
    from simgc import collect, mem_free

#########################################################
#                    SOCKET SERVER CLASS                #
#########################################################


class SocketServer:
    """
    Socket message data packet layer - send and receive
    Embedded command interpretation:
    - hello
    - version
    - exit
    - reboot
    InterpreterShell invocation with msg data
    """
    __instance = None
    __socket_interpreter_version = '0.9.9-10'

    def __new__(cls):
        """
        Singleton design pattern
        __new__ - Customize the instance creation
        cls     - class
        """
        if cls.__instance is None:
            # SocketServer singleton properties
            cls.__instance = super().__new__(cls)
            cls.__instance.name = 'SocketServer'
        return cls.__instance

    def __init__(self, host='', port=None, uid=None, user_timeout_sec=None):
        # Socket server initial parameters
        self.host = host
        self.s = None
        self.conn = None
        self.addr = None
        self.__server_console_indent = 0
        self.__auth_ok = False
        self.configure_mode = False
        # ---- Config ---
        self.pre_prompt = ""
        self.__auth_mode = cfgget('auth')
        self.__prompt = "{} $ ".format(cfgget('devfid'))
        self.__port = port if port is not None else cfgget("socport")
        self.__timeout_user = user_timeout_sec if user_timeout_sec is not None else int(cfgget("soctout"))
        self.__hwuid = uid if uid is not None else str(cfgget("hwuid"))
        # ---         ----
        self.server_console("[ socket server ] <<constructor>>")

    #####################################
    #       Socket Server Methods       #
    #####################################
    def __init_socket(self):
        """
        Socket init:
            socket create + setup as reusable (for rebind)
        """
        self.s = socket(AF_INET, SOCK_STREAM)
        self.s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    def __deinit_socket(self):
        """
        Socket deinit:
            close connection - close socket - reset console print indentation
        """
        try:
            self.conn.close()
        except Exception:
            pass
        self.s.close()

    #####################################
    #      Socket Connection Methods    #
    #####################################
    def __bind_and_accept(self):
        while True:
            try:
                self.s.bind((self.host, self.__port))
                break
            except Exception as msg:
                self.server_console('[ socket server ] Bind failed. Error Code : ' + str(msg))
                sleep(1)
        self.server_console('[ socket server ] Socket bind complete')
        self.s.listen(5)
        self.server_console('[ socket server ] Socket now listening')
        self.__accept()

    def __accept(self):
        # Reset pre prompt
        self.pre_prompt = "[password] " if self.__auth_mode else ""
        self.server_console("[ socket server ] wait to accept a connection")
        self.conn, self.addr = self.s.accept()
        self.server_console('[ socket server ] Connected with {}:{}'.format(self.addr[0], self.addr[1]))

    def __wait_for_message(self):
        prompt = "{}{} ".format(self.pre_prompt, self.__prompt).encode('utf-8')
        self.reply_message(prompt)
        self.conn.settimeout(self.__timeout_user)
        try:
            data_byte = self.conn.recv(512)
        except Exception as e:
            data_byte = b''
            if 'time' in str(e).lower() and 'out' in str(e).lower():
                self.server_console(
                    "[ socket server ] socket recv - connection with user - timeout {} sec".format(self.__timeout_user))
                self.reply_message("\n__@_/' Session timeout {} sec\nBye!".format(self.__timeout_user))
                self.__reconnect()
            else:
                raise Exception(e)
        try:
            data_str = data_byte.decode("utf-8").strip()
        except Exception:
            data_str = "ctrl-c"
        self.server_console("[ socket server ] RAW INPUT |{}|".format(data_str))
        # CALL LOW LEVEL COMMANDS -  server built-ins
        return self.__server_level_cmds(data_str)

    def __server_level_cmds(self, data_str):
        # globally available micrOS functions
        if data_str == 'exit':
            # For low level exit handling
            self.reply_message("Bye!")
            self.__reconnect()
            return ""
        if data_str == 'hello':
            # For low level device identification - hello msg
            self.reply_message("hello:{}:{}".format(cfgget('devfid'), self.__hwuid))
            return ""
        if data_str == 'version':
            # For micrOS system version info
            self.reply_message("{}".format(self.__socket_interpreter_version))
            return ""
        # Authentication handling
        data_str = self.__connection_authentication(data_str) if self.__auth_mode else data_str
        # Authenticated user functions ... shell, etc
        if data_str == 'reboot':
            self.reply_message("Reboot micrOS system.")
            self.__safe_reboot_system()
            return ""
        if data_str == 'webrepl':
            self.start_micropython_webrepl()
            return ""
        return data_str

    def __safe_reboot_system(self):
        self.server_console("Execute safe reboot: __safe_reboot_system()")
        self.reply_message("Bye!")
        self.conn.close()
        sleep(1)
        from machine import reset
        reset()
        self.__reconnect()          # In case of simulator - dummy reset

    def reply_message(self, msg):
        if isinstance(msg, bytes):
            self.conn.sendall(msg)  # conn sendall
            return
        try:
            self.conn.sendall("{}\n".format(msg).encode("utf-8"))  # conn sendall
        except Exception as e:
            self.server_console("[ socket server ] REPLY ERROR: {}".format(e))
        return

    def __reconnect(self):
        # Reset Shell
        self.configure_mode = False
        self.__server_console_indent = 0
        self.__auth_ok = False
        # Close session
        self.server_console("[ socket server ] exit and close connection from " + str(self.addr))
        self.conn.close()
        collect()
        # Accept new connection
        self.__accept()

    def run(self):
        self.server_console("[ socket server ] SERVER ADDR: telnet {} {}".format(cfgget("devip"), self.__port))
        try:
            cfgput('version', self.__socket_interpreter_version)
        except Exception as e:
            console_write("Export system version to config failed: {}".format(e))
        self.__init_socket()
        self.__bind_and_accept()
        while True:
            try:
                # Evaluate incoming msg via InterpreterShell -> InterpreterCore "Console prompt"
                is_healthy = InterpreterShell_shell(self.__wait_for_message(), SocketServerObj=self)
                if not is_healthy:
                    console_write("[EXEC-WARNING] InterpreterShell internal error.")
                    self.__recovery(is_critic=False)
            except OSError:
                # BrokenPipeError
                self.__reconnect()
            except Exception as e:
                console_write("[EXEC-ERROR] InterpreterShell error: {}".format(e))
                self.__recovery(is_critic=True)
            # Memory dimensioning dump
            self.server_console('[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: {}'.format(mem_free()))

    def __recovery(self, is_critic=False):
        """
        Handle memory errors here
        """
        self.reply_message("[HA] system recovery ...")
        collect()
        self.reply_message("[HA] gc-collect-memfree: {}".format(mem_free()))
        if is_critic:
            try:
                self.reply_message("[HA] Critical error - disconnect & hard reset")
                self.__safe_reboot_system()
            except Exception as e:
                console_write("==> [!!!][HA] Recovery error: {}".format(e))

    def server_console(self, msg):
        console_write("|" + "-" * self.__server_console_indent + msg)
        if self.__server_console_indent < 50:
            # if less then max indent
            self.__server_console_indent += 1

    def start_micropython_webrepl(self):
        self.reply_message(" Start micropython WEBREPL for interpreter web access and file transferring.")
        self.reply_message("  [!] micrOS socket shell will be available again after reboot.")
        self.reply_message("  \trestart machine shortcut: import reset")
        self.reply_message("  Connect over http://micropython.org/webrepl/#{}:8266/".format(cfgget("devip")))
        self.reply_message("  \t[!] webrepl password: {}".format(cfgget('appwd')))
        self.reply_message(" Bye!")
        try:
            import webrepl
            self.reply_message(webrepl.start(password=cfgget('appwd')))
            self.__del__()
        except Exception as e:
            self.reply_message("Error while starting webrepl: {}".format(e))

    def __connection_authentication(self, data_str):
        if not self.__auth_ok and data_str:
            # check password
            if cfgget('appwd') == data_str:
                self.__auth_ok = True
                self.reply_message("AuthOk")
                self.pre_prompt = ""
                return ""
            self.reply_message("AuthFailed\nBye!")
            self.__reconnect()
            return ""
        return data_str

    def __del__(self):
        console_write("[ socket server ] <<destructor>>")
        self.__deinit_socket()
