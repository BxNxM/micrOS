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
from InterpreterShell import shell

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
    __socket_interpreter_version = '0.10.1-1'

    def __new__(cls, host='', port=None, uid=None, user_timeout_sec=None):
        """
        Singleton design pattern
        __new__ - Customize the instance creation
        cls     - class
        """
        if SocketServer.__instance is None:
            # SocketServer singleton properties
            SocketServer.__instance = super().__new__(cls)
            # Socket server initial parameters
            SocketServer.__instance.__host = host
            SocketServer.__instance.__s = None
            SocketServer.__instance.__conn = None
            SocketServer.__instance.__addr = None
            SocketServer.__instance.__server_console_indent = 0
            SocketServer.__instance.__auth = False
            SocketServer.__instance.__isconn = False
            SocketServer.__instance.configure_mode = False
            # ---- Config ---
            SocketServer.__instance.pre_prompt = ""
            SocketServer.__instance.__auth_mode = cfgget('auth')
            SocketServer.__instance.__prompt = "{} $ ".format(cfgget('devfid'))
            SocketServer.__instance.__port = port if port is not None else cfgget("socport")
            SocketServer.__instance.__timeout_user = user_timeout_sec if user_timeout_sec is not None else int(cfgget("soctout"))
            SocketServer.__instance.__hwuid = uid if uid is not None else str(cfgget("hwuid"))
            # ---         ----
            SocketServer.__instance.server_console("[ socket server ] <<constructor>>")
        return SocketServer.__instance

    #####################################
    #       Socket Server Methods       #
    #####################################
    def __init_socket(cls):
        """
        Socket init:
        - socket create + setup as reusable (for rebind)
        - listen on socket connections
        """
        # Create and Configure socket instance
        cls.__s = socket(AF_INET, SOCK_STREAM)
        cls.__s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        # Listen up clients
        while True:
            try:
                cls.__s.bind((cls.__host, cls.__port))
                break
            except Exception as msg:
                cls.server_console('[ socket server ] Bind failed. Error Code : ' + str(msg))
                sleep(1)
        cls.server_console('[ socket server ] Socket bind complete')
        cls.__s.listen(5)
        cls.server_console('[ socket server ] Socket now listening')
        cls.__accept()

    def __close(cls):
        """
        Safe close of socket
        """
        cls.__isconn = False
        try:
            cls.__conn.close()
        except Exception:
            cls.server_console('[ socket server ] Socket was already closed.')

    def __reconnect(cls):
        # Reset shell parameters
        cls.configure_mode = False
        cls.__server_console_indent = 0
        cls.__auth = False
        # Close session
        cls.server_console("[ socket server ] exit and close connection from " + str(cls.__addr))
        cls.__close()
        # Cleanup GC Collect
        collect()
        # Accept new connection again
        cls.__accept()

    def __accept(cls):
        # Set prompt
        cls.pre_prompt = "[password] " if cls.__auth_mode else ""
        # Accept connection
        cls.server_console("[ socket server ] wait to accept a connection")
        cls.__conn, cls.__addr = cls.__s.accept()
        cls.server_console('[ socket server ] Connected with {}:{}'.format(cls.__addr[0], cls.__addr[1]))
        cls.__isconn = True

    #####################################
    #      Socket Connection Methods    #
    #####################################

    def __send_prompt(cls):
        cls.reply_message("{}{} ".format(cls.pre_prompt, cls.__prompt).encode('utf-8'))

    def __wait_for_msg(cls):
        # Check for open connection
        if cls.__conn is None: return ''
        # Reply on open connection
        cls.__send_prompt()
        cls.__conn.settimeout(cls.__timeout_user)
        # Receive msg and handle timeout
        try:
            data_byte = cls.__conn.recv(512)
        except Exception as e:
            data_byte = b''
            if 'ETIMEDOUT' in str(e).upper():
                cls.server_console(
                    "[ socket server ] socket recv - connection with user - timeout {} sec".format(cls.__timeout_user))
                cls.reply_message("\n__@_/' Session timeout {} sec\nBye!".format(cls.__timeout_user))
                cls.__reconnect()
            else:
                raise Exception(e)
        # Convert msg to str
        try:
            data_str = data_byte.decode("utf-8").strip()
        except Exception:
            data_str = 'ctrl-c'
        cls.server_console("[ socket server ] RAW INPUT |{}|".format(data_str))
        # CALL LOW LEVEL COMMANDS -  server built-ins
        return cls.__server_level_cmds(data_str)

    def __server_level_cmds(cls, data_str):
        # globally available micrOS functions
        if data_str == 'exit':
            # For low level exit handling
            cls.reply_message("Bye!")
            cls.__reconnect()
            return ""
        if data_str == 'hello':
            # For low level device identification - hello msg
            cls.reply_message("hello:{}:{}".format(cfgget('devfid'), cls.__hwuid))
            return ""
        if data_str == 'version':
            # For micrOS system version info
            cls.reply_message("{}".format(cls.__socket_interpreter_version))
            return ""
        # Authentication handling
        data_str = cls.__authentication(data_str) if cls.__auth_mode else data_str
        # Authenticated user functions ... shell, etc
        if data_str == 'reboot':
            cls.reply_message("Reboot micrOS system.")
            cls.__safe_reboot()
            return ""
        if data_str == 'webrepl':
            cls.start_micropython_webrepl()
            return ""
        return data_str

    def __safe_reboot(cls):
        cls.server_console("Execute safe reboot: __safe_reboot()")
        cls.reply_message("Bye!")
        cls.__close()
        sleep(1)
        from machine import reset
        reset()
        cls.__reconnect()          # In case of simulator - dummy reset

    def reply_message(cls, msg):
        # Skip reply if no open connection
        if not cls.__isconn:
            return
        # Reply on active connection
        try:
            if not isinstance(msg, bytes):
                msg = "{}\n".format(msg).encode("utf-8")
            cls.__conn.sendall(msg)           # conn sendall
        except Exception as e:
            cls.server_console("[ socket server ] reply error: {} -> RECONNECT".format(e))
            cls.__reconnect()
            # Send prompt after reconnect (normally runs in __wait_for_msg method)
            cls.__send_prompt()
        return

    def run(cls):
        """
        Main method, runs socket server with interpreter shell
        """
        cls.server_console("[ socket server ] SERVER ADDR: telnet {} {}".format(cfgget("devip"), cls.__port))
        try:
            cfgput('version', cls.__socket_interpreter_version)
        except Exception as e:
            console_write("Export system version to config failed: {}".format(e))
        cls.__init_socket()
        while True and cls.__isconn:
            try:
                # Evaluate incoming msg via InterpreterShell -> InterpreterCore "Console prompt"
                is_healthy = shell(cls.__wait_for_msg(), sso=cls)
                if not is_healthy:
                    console_write("[EXEC-WARNING] InterpreterShell internal error.")
                    cls.__recovery(is_critic=False)
            except OSError:
                # Broken pipe error handling
                cls.__reconnect()
            except Exception as e:
                console_write("[EXEC-ERROR] InterpreterShell error: {}".format(e))
                cls.__recovery(is_critic=True)
            # Memory dimensioning dump
            cls.server_console('[X] AFTER INTERPRETER EXECUTION FREE MEM [byte]: {}'.format(mem_free()))

    def __recovery(cls, is_critic=False):
        """
        Handle memory errors here
        """
        cls.reply_message("[HA] system recovery ...")
        collect()
        cls.reply_message("[HA] gc-collect-memfree: {}".format(mem_free()))
        if is_critic:
            cls.reply_message("[HA] Critical error - disconnect & hard reset")
            cls.__safe_reboot()

    def server_console(cls, msg):
        console_write("|" + "-" * cls.__server_console_indent + msg)
        if cls.__server_console_indent < 50:
            # if less then max indent
            cls.__server_console_indent += 1

    def start_micropython_webrepl(cls):
        cls.reply_message(" Start micropython WEBREPL for interpreter web access and file transferring.")
        cls.reply_message("  [!] micrOS socket shell will be available again after reboot.")
        cls.reply_message("  \trestart machine shortcut: import reset")
        cls.reply_message("  Connect over http://micropython.org/webrepl/#{}:8266/".format(cfgget("devip")))
        cls.reply_message("  \t[!] webrepl password: {}".format(cfgget('appwd')))
        cls.reply_message(" Bye!")
        try:
            import webrepl
            cls.reply_message(webrepl.start(password=cfgget('appwd')))
            # Deinit socket obj to make webrepl available
            cls.__del__()
        except Exception as e:
            cls.reply_message("Error while starting webrepl: {}".format(e))

    def __authentication(cls, data_str):
        if not cls.__auth and data_str:
            # check password
            if cfgget('appwd') == data_str:
                cls.__auth = True
                cls.reply_message("AuthOk")
                cls.pre_prompt = ""
                return ""
            cls.reply_message("AuthFailed\nBye!")
            cls.__reconnect()
            return ""
        return data_str

    def __del__(cls):
        console_write("[ socket server ] <<destructor>>")
        cls.__close()
        cls.__s.close()
