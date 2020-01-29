import socket
import sys
import Console
import os

try:
    import network
    Console.write("[ MICROPYTHON MODULE LOAD ] -  network - from " + str(__name__))
    sta_if = network.WLAN(network.STA_IF)
    if sta_if.active():
        server_ip = sta_if.ifconfig()[0]
    else:
        raise Exception("!!! STA IS NOT ACTIVE !!! - from " + str(__name__))
except Exception as e:
    Console.write("[ MYCROPYTHON IMPORT ERROR ] - " + str(e) + " - from " + str(__name__))
    server_ip = "ERROR"

try:
    import ConfigHandler
except Exception as e:
    Console.write("Failed to import ConfigHandler: {}".format(e))

#########################################################
#                                                       #
#               CONFIGURATION PARAMTERS                 #
#                                                       #
#########################################################
# CONFIGURATION
HOST = ''               # Symbolic name meaning all available interfaces
PORT = 9008             # Arbitrary non-privileged port
UID = "sa4r4fd4t6hg"    #TODO: get from machine

#########################################################
#                                                       #
#                    SOCKET SERVER CLASS                #
#                                                       #
#########################################################
class SocketServer():
    '''
    USER_TIMEOUT - sec
    '''
    prompt = ">>> "
    pre_prompt = ""

    def __init__(self, HOST, PORT, UID=None, USER_TIMEOUT=None):
        InterpreterShell.server_console("[ socket server ] <<constructor>>")
        self.host = HOST
        self.port = PORT
        # ---- Config ---
        self.__set_timeout_value(USER_TIMEOUT)
        self.uid = UID
        self.platform = sys.platform
        self.server_version = "0.1 beta - non secure"
        # ---         ----
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.platform == "esp8266":
            InterpreterShell.server_console("[ socket server ] telnet " + str(server_ip) + " " + str(PORT))
        else:
            InterpreterShell.server_console("[ socket server ] telnet 127.0.0.1 " + str(PORT))
        self.bind()

    def __set_timeout_value(self, USER_TIMEOUT, default_timeout=60):
        if USER_TIMEOUT is None:
            try:
                self.timeout_user = int(ConfigHandler.cfg.get("shell_timeout"))
            except Exception as e:
                self.timeout_user = default_timeout
                Console.write("Injected value (timeout <int>) error: {}".format(e))
        else:
            try:
                self.timeout_user = int(USER_TIMEOUT)
            except Exception as e:
                self.timeout_user = default_timeout
                Console.write("USER_TIMEOUT value error, must be <int>: {}".format(e))

    def bind(self):
        retry = 3
        for i in range(retry):
            try:
                self.s.bind((self.host, self.port))
                break
            except Exception as msg:
                InterpreterShell.server_console('[ socket server ] Bind failed. Error Code : ' + str(msg))
                self.port +=1
        InterpreterShell.server_console('[ socket server ] Socket bind complete')
        self.s.listen(10)
        InterpreterShell.server_console('[ socket server ] Socket now listening')
        self.accept()

    def accept(self):
        InterpreterShell.server_console("[ socket server ] wait to accept a connection - blocking call...")
        self.conn, self.addr = self.s.accept()
        InterpreterShell.server_console('[ socket server ] Connected with ' + self.addr[0] + ':' + str(self.addr[1]))

    def wait_for_message(self, receive_msg="received: "):
        prompt = SocketServer.get_prompt()
        self.repy_message(prompt)
        self.conn.settimeout(self.timeout_user)
        try:
            data_byte = self.conn.recv(1024)
        except Exception as e:
            if str(e) in "socket.timeout: timed out":
                InterpreterShell.server_console("[ socket server ] socket recv - connection with user - timeout " + str(self.timeout_user) + " sec")
                self.disconnect()
            else:
                raise e
        try:
            data_str = data_byte.decode("utf-8").strip()
        except:
            data_str = "ctrl-c"
        reply_str = receive_msg
        # AUTOMATIC REPLY:
        #reply_byte = reply_str.encode("utf-8")
        #self.repy_message(reply_byte + data_byte)
        InterpreterShell.server_console("[ socket server ] RAW INPUT |{}|".format(data_str))
        if "exit" == data_str:
            self.disconnect()
        return str(data_str)

    def repy_message(self, msg):
        if type(msg) is bytes:
            self.conn.sendall(msg)
        else:
            try:
                msg = "{}\n".format(msg)
                msg = msg.encode("utf-8")
                self.conn.sendall(msg)
            except Exception as e:
                InterpreterShell.server_console("[ socket server ] " + str(e))

    def disconnect(self):
        InterpreterShell.server_console("[ socket server ] exit and close connection from " + str(self.addr))
        self.repy_message("exit and close connection from " + str(self.addr))
        self.conn.close()
        self.accept()

    def run(self, inloop = True):
        while inloop:
            msg = self.wait_for_message()
            #self.reply_to_client("====> {}".format(msg))
            reply_msg = InterpreterShell.shell(msg)
            self.reply_to_client(reply_msg)
        if not inloop:
            msg = self.wait_for_message()
            #self.reply_to_client("====> {}".format(msg))
            reply_msg = InterpreterShell.shell(msg)
            self.reply_to_client(reply_msg)

    def reply_to_client(self, msg):
        self.repy_message(msg)

    @staticmethod
    def get_prompt():
        return "{}{} ".format(SocketServer.pre_prompt, SocketServer.prompt).encode('utf-8')

    def __del__(self):
        Console.write("[ socket server ] <<destructor>>")
        try:
            self.conn.close()
        except:
            pass
        self.s.close()

class InterpreterShell():
    serv_console_tabber = 0
    configure_mode = False

    @staticmethod
    def server_console(msg):
        Console.write("  "*InterpreterShell.serv_console_tabber + msg)
        InterpreterShell.serv_console_tabber+=1

    @staticmethod
    def shell(msg=None):
        try:
            return InterpreterShell.__shell(msg)
        except Exception as e:
            return "Runtime error: {}".format(e)

    @staticmethod
    def __shell(msg=None):
        if msg is None or msg == "":
            return ""
        msg_list = msg.strip().split()
        answer_msg = ""

        # CONFIGURE MODE
        if msg_list[0] == "configure":
            if len(msg_list) == 1:
                InterpreterShell.configure_mode = True
                SocketServer.pre_prompt = "[configure] "
            msg_list = []
        elif msg_list[0] == "noconfigure":
            if len(msg_list) == 1:
                InterpreterShell.configure_mode = False
                SocketServer.pre_prompt = ""
            msg_list = []

        # HELP MSG
        if "help" in msg_list:
            answer_msg = "Configure mode:\n"
            answer_msg += "   configure    - Enter conf mode\n"
            answer_msg += "      Key       - Get value\n"
            answer_msg += "      Key:Value - Set value\n"
            answer_msg += "      dump      - Dump all data\n"
            answer_msg += "   noconfigure - Exit conf mode\n"
            answer_msg += "Command mode:\n"
            answer_msg += LM_Handler.show_LMs_functions()
            msg_list = []

        # EXECUTE:
        # @1 Configure mode
        if InterpreterShell.configure_mode and len(msg_list) != 0:
            answer_msg = InterpreterShell.configure(msg_list)
        # @2 Command mode
        elif not InterpreterShell.configure_mode and len(msg_list) != 0:
            answer_msg = InterpreterShell.command(msg_list)

        # Return with console message
        return answer_msg

    @staticmethod
    def configure(attributes):
        return_val = ""
        # Get value
        if len(attributes) == 1:
            if attributes[0] == "dump":
                return_val = ConfigHandler.cfg.get_all()
            else:
                key = attributes[0]
                return_val = ConfigHandler.cfg.get(key)
        # Set value
        elif len(attributes) == 2:
            key = attributes[0]
            value = attributes[1]
            return_val = ConfigHandler.cfg.put(key, value)
        else:
            return_val = "Too many arguments - [1] key [2] value"
        return return_val

    @staticmethod
    def command(attributes_list):
        return LM_Handler.execute_LM_function(attributes_list)

class LM_Handler():
    '''
    Dynamic function execution
    '''

    @staticmethod
    def load_LMs():
        LM_MODULE_LIST = [i for i in os.listdir() if i.startswith('LM_')]
        LM_MODULE_LIST = [i for i in LM_MODULE_LIST if i.endswith('.py')]
        LM_MODULE_LIST = [i.replace('.py', '') for i in LM_MODULE_LIST]
        return LM_MODULE_LIST

    @staticmethod
    def show_LMs_functions():
        LMs_Funcs = ""
        for LM in LM_Handler.load_LMs():
            exec("import " + str(LM))
            LM_functions = eval("dir({})".format(LM))
            LM_functions = [i for i in LM_functions if not i.startswith('__')]
            LMs_Funcs += "   {}\n".format(LM)
            for func in LM_functions:
                LMs_Funcs += "   {}{}\n".format(" "*len(LM), func)
        return LMs_Funcs

    @staticmethod
    def execute_LM_function(argument_list):
        '''
        1. param. - LM name, i.e. LM_commands
        2. param. - function call with parameters, i.e. a()
        '''
        if len(argument_list) >= 2:
            LM_name = argument_list[0]
            LM_function = argument_list[1]
        try:
            print("{}.{}".format(LM_name, LM_function))
            exec("import " + str(LM_name))
            return str(eval("{}.{}".format(LM_name, LM_function)))
        except Exception as e:
            return str(e)

try:
    if __name__ == "__main__":
        server = SocketServer(HOST, PORT, UID)
        server.run()
    if "WebServer" in __name__:
        server = SocketServer(HOST, PORT, UID)
        #server.run()
except KeyboardInterrupt:
        server.__del__()
