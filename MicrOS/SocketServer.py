from sys import platform
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from gc import collect
from InterpreterShell import shell as InterpreterShell_shell

#########################################################
#                         IMPORTS                       #
#########################################################
try:
    from ConfigHandler import console_write, cfgget, cfgput
except Exception as e:
    print("Failed to import ConfigHandler: {}".format(e))
    console_write = None

try:
    from network import WLAN, STA_IF
    console_write("[ MICROPYTHON MODULE LOAD ] -  network - from " + str(__name__))
    sta_if = WLAN(STA_IF)
except Exception as e:
    console_write("[ MYCROPYTHON IMPORT ERROR ] - " + str(e) + " - from " + str(__name__))
    sta_if = None

#########################################################
#                    SOCKET SERVER CLASS                #
#########################################################
class SocketServer():
    '''
    USER_TIMEOUT - sec
    '''
    prompt = "{} $ ".format(cfgget('devfid'))

    def __init__(self, HOST='', PORT=None, UID=None, USER_TIMEOUT=None):
        self.CONFIGURE_MODE = False
        self.pre_prompt = ""
        self.server_console_indent = 0
        self.server_console("[ socket server ] <<constructor>>")
        self.host = HOST
        self.port = self.__set_port_from_config(PORT)
        # ---- Config ---
        self.__set_timeout_value(USER_TIMEOUT)
        self.get_uid_macaddr_hex(UID)
        # ---         ----
        self.init_socket()
        if "esp" in platform:
            self.server_console("[ socket server ] telnet " + str(cfgget("devip")) + " " + str(self.port))
        else:
            self.server_console("[ socket server ] telnet 127.0.0.1 " + str(self.port))

    def init_socket(self):
        self.s = socket(AF_INET, SOCK_STREAM)

    def get_uid_macaddr_hex(self, UID=None):
        if UID is not None:
            self.uid = UID
        elif sta_if is not None:
            mac = sta_if.config('mac')
            self.uid = ""
            for ot in list(mac):
                self.uid += hex(ot)
        else:
            self.uid = "n/a"
        cfgput("hwuid", self.uid)

    def __set_port_from_config(self, PORT):
        if PORT is None:
            return int(cfgget("socport"))
        else:
            return int(PORT)

    def __set_timeout_value(self, USER_TIMEOUT, default_timeout=60):
        if USER_TIMEOUT is None:
            try:
                self.timeout_user = int(cfgget("soctout"))
            except Exception as e:
                self.timeout_user = default_timeout
                console_write("Injected value (timeout <int>) error: {}".format(e))
        else:
            try:
                self.timeout_user = int(USER_TIMEOUT)
            except Exception as e:
                self.timeout_user = default_timeout
                console_write("USER_TIMEOUT value error, must be <int>: {}".format(e))

    def bind(self):
        retry = 6
        for i in range(retry):
            try:
                self.s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                self.s.bind((self.host, self.port))
                break
            except Exception as msg:
                self.server_console('[ socket server ] Bind failed. Error Code : ' + str(msg))
        self.server_console('[ socket server ] Socket bind complete')
        self.s.listen(10)
        self.server_console('[ socket server ] Socket now listening')
        self.accept()

    def accept(self):
        self.server_console("[ socket server ] wait to accept a connection - blocking call...")
        self.conn, self.addr = self.s.accept()
        self.server_console('[ socket server ] Connected with ' + self.addr[0] + ':' + str(self.addr[1]))

    def wait_for_message(self, receive_msg="received: "):
        prompt = self.get_prompt()
        self.reply_message(prompt)
        self.conn.settimeout(self.timeout_user)
        try:
            data_byte = self.conn.recv(1024)
        except Exception as e:
            if "TIMEDOUT" in str(e) or "timoeout" in str(e):
                self.server_console("[ socket server ] socket recv - connection with user - timeout " + str(self.timeout_user) + " sec")
                self.reply_message("Session timeout {} sec".format(self.timeout_user))
                self.disconnect()
            else:
                raise e
        try:
            data_str = data_byte.decode("utf-8").strip()
        except:
            data_str = "ctrl-c"
        reply_str = receive_msg
        self.server_console("[ socket server ] RAW INPUT |{}|".format(data_str))
        if "exit" == data_str:
            # For low level exit handling
            self.reply_message("Bye!")
            self.disconnect()
            data_str = ""
        if "hello" == data_str:
            # For low level device identification - hello msg
            self.reply_message("hello:{}:{}".format(cfgget('devfid'), self.uid))
            data_str = ""
        return str(data_str)

    def reply_message(self, msg):
        if len(str(msg).strip()) == 0:
            self.server_console("[ socket server ] No msg income: {}".format(msg))
            return
        if type(msg) is bytes:
            self.conn.sendall(msg)
        else:
            try:
                msg = "{}\n".format(msg)
                msg = msg.encode("utf-8")
                self.conn.sendall(msg)
            except Exception as e:
                self.server_console("[ socket server ] " + str(e))

    def disconnect(self):
        # Close session
        self.server_console("[ socket server ] exit and close connection from " + str(self.addr))
        self.reply_message("exit and close connection from " + str(self.addr))
        self.conn.close()
        # Reset Shell & prompt
        try:
            self.CONFIGURE_MODE = False
            collect()
        except Exception as e:
            console_write("[ERROR] gc collect: " + str(e))
        self.pre_prompt = ""
        self.server_console_indent = 0
        # Accept new connection
        self.accept()

    def run(self, inloop = True):
        self.bind()
        while inloop:
            try:
                is_healthy, msg = InterpreterShell_shell(self.wait_for_message(), SocketServerObj=self)
                if not is_healthy:
                    console_write("==> InterpreterShell error: " + str(msg))
            except Exception as e:
                console_write("[REINIT] SocketServer error: " + str(e))
                collect()               # gc collect
                self.disconnect()
                #self.deinit_socket()
                #self.init_socket()
                #self.bind()
        if not inloop:
            is_healthy, msg = InterpreterShell_shell(self.wait_for_message(), SocketServerObj=self)
            del is_healthy

    def get_prompt(self):
        return "{}{} ".format(self.pre_prompt, SocketServer.prompt).encode('utf-8')

    def server_console(self, msg):
        console_write("  "*self.server_console_indent + msg)
        self.server_console_indent+=1

    def deinit_socket(self):
        self.server_console_indent = 0
        try:
            self.conn.close()
        except:
            pass
        self.s.close()

    def __del__(self):
        console_write("[ socket server ] <<destructor>>")
        self.deinit_socket()

#########################################################
#                       MODULE INIT                     #
#########################################################
def main():
    server = SocketServer()
    server.run()

try:
    if __name__ == "__main__":
        main()
    if "SocketServer" in __name__:
        server = SocketServer()
        #server.run()
except KeyboardInterrupt:
    console_write("Keyboard interrupt in SocketServer.")
