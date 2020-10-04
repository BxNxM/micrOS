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

from sys import platform
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from time import sleep
from ConfigHandler import console_write, cfgget, cfgput
from InterpreterShell import shell as InterpreterShell_shell

try:
    from gc import collect, mem_free
except Exception as e:
    print("Failed to import gc: {}".format(e))
    collect = None
    mem_free = None


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
    __socket_interpreter_version = '0.1.6-0'

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
        self.server_console_indent = 0
        self.CONFIGURE_MODE = False
        self.pre_prompt = ""
        self.host = host
        self.s = None
        self.conn = None
        self.addr = None
        # ---- Config ---
        self.prompt = "{} $ ".format(cfgget('devfid'))
        self.port = port if port is not None else cfgget("socport")
        self.timeout_user = user_timeout_sec if user_timeout_sec is not None else int(cfgget("soctout"))
        self.uid = uid if uid is not None else str(cfgget("hwuid"))
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
                self.s.bind((self.host, self.port))
                break
            except Exception as msg:
                self.server_console('[ socket server ] Bind failed. Error Code : ' + str(msg))
                sleep(1)
        self.server_console('[ socket server ] Socket bind complete')
        self.s.listen(10)
        self.server_console('[ socket server ] Socket now listening')
        self.__accept()

    def __accept(self):
        self.server_console("[ socket server ] wait to accept a connection - blocking call...")
        self.conn, self.addr = self.s.accept()
        self.server_console('[ socket server ] Connected with {}:{}'.format(self.addr[0], self.addr[1]))

    def __wait_for_message(self):
        prompt = "{}{} ".format(self.pre_prompt, self.prompt).encode('utf-8')
        self.reply_message(prompt)
        self.conn.settimeout(self.timeout_user)
        try:
            data_byte = self.conn.recv(512)
        except Exception as e:
            data_byte = b''
            if "TIMEDOUT" in str(e) or "timoeout" in str(e):
                self.server_console(
                    "[ socket server ] socket recv - connection with user - timeout {} sec".format(self.timeout_user))
                self.reply_message("Session timeout {} sec".format(self.timeout_user))
                self.__reconnect()
            else:
                raise Exception(e)
        try:
            data_str = data_byte.decode("utf-8").strip()
        except Exception:
            data_str = "ctrl-c"
        self.server_console("[ socket server ] RAW INPUT |{}|".format(data_str))
        if data_str == 'exit':
            # For low level exit handling
            data_str = ""
            self.reply_message("Bye!")
            self.__reconnect()
        if data_str == 'hello':
            # For low level device identification - hello msg
            data_str = ""
            self.reply_message("hello:{}:{}".format(cfgget('devfid'), self.uid))
        if data_str == 'version':
            # For micrOS system version info
            data_str = ""
            self.reply_message("{}".format(self.__socket_interpreter_version))
        if data_str == 'reboot':
            data_str = ""
            self.reply_message("Reboot micrOS system.")
            self.__safe_reboot_system()
        if data_str == 'webrepl':
            data_str = ""
            self.reply_message(self.start_micropython_webrepl())
        return str(data_str)

    def __safe_reboot_system(self):
        self.server_console("Execute safe reboot: __safe_reboot_system()")
        self.reply_message("System is rebooting now, bye :)")
        self.conn.close()
        if 'esp' in platform:
            sleep(1)
            from machine import reset
            reset()
        else:
            self.__reconnect()

    def reply_message(self, msg):
        if isinstance(msg, bytes):
            self.conn.sendall(msg)  # conn sendall
        else:
            try:
                msg = "{}\n".format(msg)
                msg = msg.encode("utf-8")
                self.conn.sendall(msg)  # conn sendall
            except Exception as e:
                self.server_console("[ socket server ] REPLY ERROR: {}".format(e))

    def __reconnect(self):
        # Close session
        self.server_console("[ socket server ] exit and close connection from " + str(self.addr))
        try:
            self.reply_message("exit and close connection from " + str(self.addr))
        except Exception: pass
        self.conn.close()
        # Reset Shell & prompt
        self.CONFIGURE_MODE = False
        if collect is not None: collect()
        self.pre_prompt = ""
        self.server_console_indent = 0
        # Accept new connection
        self.__accept()

    def run(self):
        if "esp" in platform:
            self.server_console("[ socket server ] SERVER ADDR: telnet {} {}".format(cfgget("devip"), self.port))
        else:
            self.server_console("[ socket server ] SERVER ADDR: telnet 127.0.0.1 " + str(self.port))

        try:
            cfgput('version', self.__socket_interpreter_version)
        except Exception as e:
            console_write("Export system version to config failed: {}".format(e))
        self.__init_socket()
        self.__bind_and_accept()
        while True:
            try:
                # Evaluate incoming msg via InterpreterShell -> InterpreterCore "Console prompt"
                is_healthy, msg = InterpreterShell_shell(self.__wait_for_message(), SocketServerObj=self)
                if not is_healthy:
                    console_write("[EXEC-WARNING] InterpreterShell internal error: {}".format(msg))
                    self.__recovery(errlvl=0)
            except OSError:
                # BrokenPipeError
                self.__reconnect()
            except Exception as e:
                console_write("[EXEC-ERROR] InterpreterShell error: {}".format(e))
                self.__recovery(errlvl=1)
            # Memory dimensioning dump
            if mem_free is not None:
                self.server_console('[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: {}'.format(mem_free()))

    def __recovery(self, errlvl=0):
        """
        Handle memory errors here
        """
        self.reply_message("[HA] system recovery ...")
        if 'esp' in platform:
            collect()
            self.reply_message("[HA] gc-collect-memfree: {}".format(mem_free()))
            if errlvl == 1:
                try:
                    self.reply_message("[HA] Critical error - disconnect & hard reset")
                    self.__safe_reboot_system()
                except Exception as e:
                    console_write("==> [!!!][HA] Recovery error: {}".format(e))
        else:
            console_write("[HA] recovery only available on esp - nodemcu")

    def server_console(self, msg):
        console_write("|" + "-" * self.server_console_indent + msg)
        if self.server_console_indent < 50:
            # if less then max indent
            self.server_console_indent += 1

    def __del__(self):
        console_write("[ socket server ] <<destructor>>")
        self.__deinit_socket()

    def start_micropython_webrepl(self):
        self.reply_message(" Start micropython WEBREPL for interpreter web access and file transferring.")
        self.reply_message("  [!] micrOS socket shell will be available again after reboot.")
        self.reply_message("  \trestart machine shortcut: import reset")
        self.reply_message("  Connect over http://micropython.org/webrepl/ ws://{}:8266".format(cfgget("devip")))
        self.reply_message("  \t[!] webrepl password: {}".format(cfgget('appwd')))
        self.reply_message(" See you soon! :)")
        self.__deinit_socket()
        try:
            import webrepl
            self.reply_message(webrepl.start(password=cfgget('appwd')))
        except Exception as e:
            return e
        return True

#########################################################
#                 MAIN (FOR TEST REASONS)               #
#########################################################


if __name__ == "__main__":
    try:
        server = SocketServer()
        server.run()
    except KeyboardInterrupt:
        console_write("Keyboard interrupt in SocketServer.")
