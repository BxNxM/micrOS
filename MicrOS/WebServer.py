import socket
import sys
import os

#########################################################
#                         IMPORTS                       #
#########################################################
try:
    import ConfigHandler
except Exception as e:
    print("Failed to import ConfigHandler: {}".format(e))

try:
    import network
    ConfigHandler.console_write("[ MICROPYTHON MODULE LOAD ] -  network - from " + str(__name__))
    sta_if = network.WLAN(network.STA_IF)
    if sta_if.active():
        server_ip = sta_if.ifconfig()[0]
    else:
        raise Exception("!!! STA IS NOT ACTIVE !!! - from " + str(__name__))
except Exception as e:
    ConfigHandler.console_write("[ MYCROPYTHON IMPORT ERROR ] - " + str(e) + " - from " + str(__name__))
    server_ip = "ERROR"

try:
    from InterpreterShell import reset_shell_state as InterpreterShell_reset_shell_state
    from InterpreterShell import shell as InterpreterShell_shell
except Exception as e:
    ConfigHandler.console_write("InterpreterShell import error: {}".format(e))

#########################################################
#               CONFIGURATION PARAMTERS                 #
#########################################################
# CONFIGURATION
HOST = ''               # Symbolic name meaning all available interfaces
PORT = 9008             # Arbitrary non-privileged port
UID = "sa4r4fd4t6hg"    #TODO: get from machine

#########################################################
#                    SOCKET SERVER CLASS                #
#########################################################
class SocketServer():
    '''
    USER_TIMEOUT - sec
    '''
    prompt = ">>> "

    def __init__(self, HOST, PORT, UID=None, USER_TIMEOUT=None):
        self.pre_prompt = ""
        self.server_console_indent = 0
        self.server_console("[ socket server ] <<constructor>>")
        self.host = HOST
        self.port = PORT
        # ---- Config ---
        self.__set_timeout_value(USER_TIMEOUT)
        self.uid = UID
        self.platform = sys.platform
        # ---         ----
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.platform == "esp8266":
            self.server_console("[ socket server ] telnet " + str(server_ip) + " " + str(PORT))
        else:
            self.server_console("[ socket server ] telnet 127.0.0.1 " + str(PORT))
        self.bind()

    def __set_timeout_value(self, USER_TIMEOUT, default_timeout=60):
        if USER_TIMEOUT is None:
            try:
                self.timeout_user = int(ConfigHandler.cfg.get("shell_timeout"))
            except Exception as e:
                self.timeout_user = default_timeout
                ConfigHandler.console_write("Injected value (timeout <int>) error: {}".format(e))
        else:
            try:
                self.timeout_user = int(USER_TIMEOUT)
            except Exception as e:
                self.timeout_user = default_timeout
                ConfigHandler.console_write("USER_TIMEOUT value error, must be <int>: {}".format(e))

    def bind(self):
        retry = 3
        for i in range(retry):
            try:
                self.s.bind((self.host, self.port))
                break
            except Exception as msg:
                self.server_console('[ socket server ] Bind failed. Error Code : ' + str(msg))
                self.port +=1
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
            if str(e) in "socket.timeout: timed out":
                self.server_console("[ socket server ] socket recv - connection with user - timeout " + str(self.timeout_user) + " sec")
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
            self.disconnect()
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
        InterpreterShell_reset_shell_state()
        self.pre_prompt = ""
        self.server_console_indent = 0
        # Accept new connection
        self.accept()

    def run(self, inloop = True):
        while inloop:
            msg = self.wait_for_message()
            reply_msg = InterpreterShell_shell(msg, WebServerObj=self)
            if reply_msg is not None:
                self.reply_message(reply_msg)
        if not inloop:
            msg = self.wait_for_message()
            reply_msg = InterpreterShell_shell(msg, WebServerObj=self)
            self.reply_message(reply_msg)

    def get_prompt(self):
        return "{}{} ".format(self.pre_prompt, SocketServer.prompt).encode('utf-8')

    def server_console(self, msg):
        ConfigHandler.console_write("  "*self.server_console_indent + msg)
        self.server_console_indent+=1

    def __del__(self):
        ConfigHandler.console_write("[ socket server ] <<destructor>>")
        try:
            self.conn.close()
        except:
            pass
        #self.s.close()

#########################################################
#                       MODULE INIT                     #
#########################################################
def main():
    server = SocketServer(HOST, PORT, UID)
    server.run()

try:
    if __name__ == "__main__":
        main()
    if "WebServer" in __name__:
        server = SocketServer(HOST, PORT, UID)
        #server.run()
except KeyboardInterrupt:
        server.__del__()
