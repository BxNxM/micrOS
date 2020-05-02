#########################################################
#                         IMPORTS                       #
#########################################################

from sys import platform
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from ConfigHandler import console_write, cfgget, cfgput
from InterpreterShell import shell as InterpreterShell_shell
from time import sleep
from Hooks import profiling_info

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
    InterpreterShell invocation with msg
    """
    __instance = None
    __socket_interpreter_version = '0.0.9-22'

    def __new__(cls, host='', port=None, uid=None, user_timeout_sec=None):
        # cls - first parameter for class method, instead of cls
        if cls.__instance is None:
            # SocketServer singleton properties
            cls.__instance = super().__new__(cls)
            cls.__instance.name = 'SocketServer'
            # Socket server initial parameters
            cls.__instance.server_console_indent = 0
            cls.__instance.CONFIGURE_MODE = False
            cls.__instance.pre_prompt = ""
            cls.__instance.host = host
            cls.__instance.s = None
            cls.__instance.conn = None
            # ---- Config ---
            cls.__instance.prompt = "{} $ ".format(cfgget('devfid'))
            cls.__instance.port = port if port is not None else cfgget("socport")
            cls.__instance.timeout_user = user_timeout_sec if user_timeout_sec is not None else int(cfgget("soctout"))
            cls.__instance.uid = uid if uid is not None else str(cfgget("hwuid"))
            # ---         ----
            cls.__instance.server_console("[ socket server ] <<constructor>>")
        return cls.__instance

    #####################################
    #       Socket Server Methods       #
    #####################################
    def __init_socket(cls):
        """
        Socket init:
            socket create + setup as reusable (for rebind)
        """
        cls.s = socket(AF_INET, SOCK_STREAM)
        cls.s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    def __deinit_socket(cls):
        """
        Socket deinit:
            close connection - close socket - reset console print indentation
        """
        try:
            cls.conn.close()
        except Exception:
            pass
        cls.s.close()

    #####################################
    #      Socket Connection Methods    #
    #####################################
    def __bind_and_accept(cls):
        while True:
            try:
                cls.s.bind((cls.host, cls.port))
                break
            except Exception as msg:
                cls.server_console('[ socket server ] Bind failed. Error Code : ' + str(msg))
                sleep(1)
        cls.server_console('[ socket server ] Socket bind complete')
        cls.s.listen(10)
        cls.server_console('[ socket server ] Socket now listening')
        cls.__accept()

    def __accept(cls):
        cls.server_console("[ socket server ] wait to accept a connection - blocking call...")
        cls.conn, cls.addr = cls.s.accept()
        cls.server_console('[ socket server ] Connected with ' + cls.addr[0] + ':' + str(cls.addr[1]))

    def __wait_for_message(cls):
        prompt = "{}{} ".format(cls.pre_prompt, cls.prompt).encode('utf-8')
        cls.reply_message(prompt)
        cls.conn.settimeout(cls.timeout_user)
        try:
            data_byte = cls.conn.recv(512)
        except Exception as e:
            data_byte = b''
            if "TIMEDOUT" in str(e) or "timoeout" in str(e):
                cls.server_console(
                    "[ socket server ] socket recv - connection with user - timeout " + str(cls.timeout_user) + " sec")
                cls.reply_message("Session timeout {} sec".format(cls.timeout_user))
                cls.__reconnect()
            else:
                raise Exception(e)
        try:
            data_str = data_byte.decode("utf-8").strip()
        except Exception:
            data_str = "ctrl-c"
        cls.server_console("[ socket server ] RAW INPUT |{}|".format(data_str))
        if "exit" == data_str:
            # For low level exit handling
            data_str = ""
            cls.reply_message("Bye!")
            cls.__reconnect()
        if "hello" == data_str:
            # For low level device identification - hello msg
            data_str = ""
            cls.reply_message("hello:{}:{}".format(cfgget('devfid'), cls.uid))
        if "version" == data_str:
            # For MicrOS system version info
            data_str = ""
            cls.reply_message("{}".format(cls.__socket_interpreter_version))
        if "reboot" == data_str:
            data_str = ""
            cls.reply_message("Reboot MicrOS system.")
            cls.__safe_reboot_system()
        return str(data_str)

    def __safe_reboot_system(cls):
        cls.server_console("Execute safe reboot: __safe_reboot_system()")
        cls.reply_message("System is rebooting now, bye :)")
        cls.conn.close()
        if 'esp' in platform:
            sleep(1)
            from machine import reset
            reset()
        else:
            cls.__reconnect()

    def reply_message(cls, msg):
        if type(msg) is bytes:
            cls.conn.sendall(msg)  # conn sendall
        else:
            try:
                msg = "{}\n".format(msg)
                msg = msg.encode("utf-8")
                cls.conn.sendall(msg)  # conn sendall
            except Exception as e:
                cls.server_console("[ socket server ] REPLY ERROR: {}".format(e))

    def __reconnect(cls):
        # Close session
        cls.server_console("[ socket server ] exit and close connection from " + str(cls.addr))
        try:
            cls.reply_message("exit and close connection from " + str(cls.addr))
        except Exception: pass
        cls.conn.close()
        # Reset Shell & prompt
        try:
            cls.CONFIGURE_MODE = False
            collect()
        except Exception as e:
            console_write("[ERROR] gc collect: " + str(e))
        cls.pre_prompt = ""
        cls.server_console_indent = 0
        # Accept new connection
        cls.__accept()

    def run(cls):
        if "esp" in platform:
            cls.server_console("[ socket server ] SERVER ADDR: telnet " + str(cfgget("devip")) + " " + str(cls.port))
        else:
            cls.server_console("[ socket server ] SERVER ADDR: telnet 127.0.0.1 " + str(cls.port))

        try:
            cfgput('version', cls.__socket_interpreter_version)
        except Exception as e:
            console_write("Export system version to config failed: {}".format(e))
        cls.__init_socket()
        cls.__bind_and_accept()
        while True:
            try:
                # Evaluate incoming msg via InterpreterShell -> InterpreterCore "Console prompt"
                is_healthy, msg = InterpreterShell_shell(cls.__wait_for_message(), SocketServerObj=cls.__instance)
                if not is_healthy:
                    console_write("[EXEC-WARNING] InterpreterShell internal error: {}".format(msg))
                    cls.__recovery(errlvl=0)
            except OSError:
                # BrokenPipeError
                cls.__reconnect()
            except Exception as e:
                console_write("[EXEC-ERROR] InterpreterShell error: {}".format(e))
                cls.__recovery(errlvl=1)
            profiling_info(label='[X] AFTER INTERPRETER EXECUTION')

    def __recovery(cls, errlvl=0):
        """
        Handle memory errors here
        """
        cls.reply_message("[HA] system recovery ...")
        if 'esp' in platform:
            collect()
            cls.reply_message("[HA] gc-ollect-memfree: {}".format(mem_free()))
            if errlvl == 1:
                try:
                    cls.reply_message("[HA] Critical error - disconnect & hard reset")
                    cls.__safe_reboot_system()
                except Exception as e:
                    console_write("==> [!!!][HA] Recovery error: {}".format(e))
        else:
            console_write("[HA] recovery only available on esp - nodemcu")

    def server_console(cls, msg):
        console_write("|" + "-" * cls.server_console_indent + msg)
        cls.server_console_indent += 1

    def __del__(cls):
        console_write("[ socket server ] <<destructor>>")
        cls.__deinit_socket()


#########################################################
#                 MAIN (FOR TEST REASONS)               #
#########################################################


if __name__ == "__main__":
    try:
        server = SocketServer()
        server.run()
    except KeyboardInterrupt:
        console_write("Keyboard interrupt in SocketServer.")
