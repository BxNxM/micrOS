import socket
import sys
# Try to import - SUCCESS if we are on micropython
try:
    import network
    print("[ MICROPYTHON MODULE LOAD ] -  network - from " + str(__name__))
    sta_if = network.WLAN(network.STA_IF)
    if sta_if.active():
        server_ip = sta_if.ifconfig()[0]
    else:
        raise Exception("!!! STA IS NOT ACTIVE !!! - from " + str(__name__))
except Exception as e:
    print("[ MYCROPYTHON IMPORT ERROR ] - " + str(e) + " - from " + str(__name__))
    server_ip = "ERROR"

try:
    import ConfigHandler
    print("[ MICROPYTHON MODULE LOAD ] -  ConfigHandler - from " + str(__name__))
except Exception as e:
    print("[ MYCROPYTHON IMPORT ERROR ] - " + str(e) + " - from " + str(__name__))
    ConfigHandler = None
#########################################################
#                                                       #
#               CONFIGURATION PARAMTERS                 #
#                                                       #
#########################################################
# CONFIGURATION
HOST = ''   # Symbolic name meaning all available interfaces
PORT = 9008 # Arbitrary non-privileged port
USER_TIMEOUT = 100              #sec
UID = "sa4r4fd4t6hg"            #TODO: get from machine
ID = "TestDevice"

#########################################################
#                                                       #
#                    SOCKET SERVER CLASS                #
#                                                       #
#########################################################
class live_server():
    def __init__(self, HOST, PORT, USER_TIMEOUT, UID, ID):
        interpreter_shell.server_console("[ socket server ] <<constructor>>")
        self.host = HOST
        self.port = PORT
        # ---- Config ---
        self.timeout_user = USER_TIMEOUT
        self.uid = UID
        self.id = ID
        self.platform = sys.platform
        self.live_server_version = "0.1 beta - non secure"
        self.shell_version = "0.1 beta - non secure"
        # ---        ----
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.platform == "esp8266":
            interpreter_shell.server_console("[ socket server ] telnet " + str(server_ip) + " " + str(PORT))
        else:
            interpreter_shell.server_console("[ socket server ] telnet 127.0.0.1 " + str(PORT))
        self.bind()

    def bind(self):
        try:
            self.s.bind((self.host, self.port))
        except Exception as msg:
            interpreter_shell.server_console('[ socket server ] Bind failed. Error Code : ' + str(msg))
        interpreter_shell.server_console('[ socket server ] Socket bind complete')
        self.s.listen(10)
        interpreter_shell.server_console('[ socket server ] Socket now listening')
        self.accept()

    def accept(self):
        interpreter_shell.server_console("[ socket server ] wait to accept a connection - blocking call...")
        self.conn, self.addr = self.s.accept()
        interpreter_shell.server_console('[ socket server ] Connected with ' + self.addr[0] + ':' + str(self.addr[1]))

    def wait_for_message(self, receive_msg="received: "):
        prompt = ">>> ".encode('utf-8')
        self.repy_message(prompt)
        self.conn.settimeout(self.timeout_user)
        try:
            data_byte = self.conn.recv(1024)
        except Exception as e:
            if str(e) in "socket.timeout: timed out":
                interpreter_shell.server_console("[ socket server ] socket recv - connection with user - timeout " + str(self.timeout_user) + " sec")
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
        interpreter_shell.server_console("[ socket server ] RAW INPUT |" + data_str +"|")
        if "exit" == data_str:
            self.disconnect()
        return str(data_str)

    def repy_message(self, msg):
        if type(msg) is bytes:
            self.conn.sendall(msg)
        else:
            try:
                msg += "\n"
                msg = msg.encode("utf-8")
                self.conn.sendall(msg)
            except Exception as e:
                interpreter_shell.server_console("[ socket server ] " + str(e))

    def disconnect(self):
        interpreter_shell.server_console("[ socket server ] exit and close connection from " + str(self.addr))
        self.repy_message("exit and close connection from " + str(self.addr))
        self.conn.close()
        self.accept()

    def run(self, inloop = True):
        while inloop:
            msg = self.wait_for_message()
            interpreter_shell.shell(msg, self)
        if not inloop:
            msg = self.wait_for_message()
            interpreter_shell.shell(msg, self)

    def __del__(self):
        print("[ socket server ] <<destructor>>")
        try:
            self.conn.close()
        except:
            pass
        self.s.close()

#########################################################
#                                                       #
#                    SHELL / INTERPRETER                #
#                                                       #
#########################################################
class interpreter_shell():
    # AVAIBLE COMMANDS FROM SHELL PROMPT
    cmd_dict={  "exit": None,
                "help": "interpreter_shell.help",
                "echo": "interpreter_shell.echo",
                "version": "interpreter_shell.version",
                "config": "interpreter_shell.config",
                "exec": "interpreter_shell.execute"}
    serv_console_tabber=0

    @staticmethod
    def shell(msg, server):
        input_list = msg.split(' ')
        exec_output = "None"
        #first_cmd = msg.split(' ', 1)[0]
        if input_list[0] == "exit":
            return
        interpreter_shell.serv_console_tabber = 0
        if input_list[0] in interpreter_shell.cmd_dict.keys():
            interpreter_shell.server_console("[shell] >>> key:" + str(input_list[0]) + " value :::EXECUTE::: " + str(interpreter_shell.cmd_dict[input_list[0]]))
            # IF ARGUMENTS ADDED
            if len(input_list) > 1:
                try:
                    # get args string
                    args = '"' + msg.split(' ', 1)[1] + '"'
                    interpreter_shell.server_console("args: " + args)
                    # EXECUTION
                    exec_output = eval(interpreter_shell.cmd_dict[input_list[0]]+"(server," + str(args) + ")")
                    interpreter_shell.server_console("exec " + str(interpreter_shell.cmd_dict[input_list[0]])+"(server," + str(args) + ")")
                except Exception as err:
                    interpreter_shell.server_console("ERROR: " + str(err))
                    server.repy_message(str(err))
            # RUN WITHOUT ARGUMENTS
            else:
                try:
                    # EXECUTION
                    exec_output = eval(interpreter_shell.cmd_dict[input_list[0]]+"(server)")
                    interpreter_shell.server_console("exec " + str(interpreter_shell.cmd_dict[input_list[0]]+"(server)"))
                except Exception as err:
                    interpreter_shell.server_console("ERROR" + str(err))
                    server.repy_message(str(err))
            # return output to client and to the console
            interpreter_shell.server_console(str(exec_output))
            server.repy_message(str(exec_output))
        else:
            error_msg = "-shell: " + str(msg) + ": command not found Try: help"
            interpreter_shell.server_console(error_msg)
            server.repy_message(error_msg)

    @staticmethod
    def help(server):
        text = "AVAIBLE COMMANDS:\n"
        try:
            return text + str(Plugins.ConfigHandler_get("micrOs_manual"))
        except Exception as e:
            return text + " manual key not in node_config.cfg file! " + str(e)

    @staticmethod
    def echo(server, string=""):
            if string == "":
                return "missing input argument\n...Try: echo hello world!"
            interpreter_shell.server_console("echo " + string)
            return str(string)

    @staticmethod
    def version(server):
        version = "LIVE SERVER:\t" + server.live_server_version + "\n"
        version += "SHELL:\t\t" + server.shell_version + "\n"
        version += "PLATFORM:\t" + str(server.platform)
        return str(version)

    @staticmethod
    def config(server, param=""):
        config_dict_ext = {}
        config_dict =   {"timeout_user": 'server.timeout_user',
                         "uid": 'server.uid',
                         "id": 'server.id',
                         "man": "TODO"}
        # load config handler dict
        config_dict_ext = Plugins.ConfigHandlerPlugin_load()
        # merge dicts
        config_dict = {**config_dict, **config_dict_ext}

        param_list = param.split(" ")
        is_found = True
        # run without parameters - default
        if param == "":
            msg = Plugins.config_manual_generator(config_dict)
            return msg + "\n...for more info Try: config man"
        # is paramters added
        for cmd, function in config_dict.items():
            # if parameter is valid
            if param_list[0] == cmd and len(param_list) == 1:
                # if parameter value request was lounched
                try:
                    # if parameter is string with execution
                    return str(eval(config_dict[cmd]))
                except:
                    # if parameter is executable - simple value
                    return config_dict[cmd]
            # if parameter is valid and value set request was lounched
            elif param_list[0] == cmd and len(param_list) == 3:
                if param_list[1] == "=":
                    try:
                        # if input number OK
                        value = int(param_list[2])
                    except:
                        # if input string... convert for exec
                        value = '"' + str(param_list[2]) + '"'
                    # timeout_user parameter must be integer!
                    if param_list[0] == "timeout_user" and  not ("int" in str(type(value))):
                        return "timeout_user must be integer!"
                    set_cmd = config_dict[cmd] + " = " + str(value)
                    try:
                        # set value is simple variable
                        exec(set_cmd)
                    except:
                        # set with plugin, ConfigHandler
                        Plugins.ConfigHandler_var(cmd, param_list[2])
                    # return value from variable
                    return str(eval(config_dict[cmd]))
            else:
                is_found = False
        if not is_found:
            return str(param_list) + " unknown argument"

    @staticmethod
    def execute(server, string=""):
        args_list = string.split(' ')
        if len(args_list) == 2:
            module_for_import = args_list[0]
            run_function_from_module = args_list[1]
            try:
                exec("import " + str(module_for_import))
                return str(eval(run_function_from_module))
            except Exception as e:
                return str(e)
        else:
            return "Not enough parameter <2> required!\nmodule_for_import and run_function_from_module"

    # server side submethod
    @staticmethod
    def server_console(msg):
        print("  "*interpreter_shell.serv_console_tabber + msg)
        interpreter_shell.serv_console_tabber+=1


class Plugins():
    """ EXTERNAL micrOs MODULES HANDLING """

    @staticmethod
    def ConfigHandlerPlugin_load():
        if ConfigHandler is not None:
            conf_dict = ConfigHandler.cfg.get_all()
            for key, value in conf_dict.items():
                conf_dict[key] = 'Plugins.ConfigHandler_get("' + str(key) + '")'
            return conf_dict
        else:
            return {}

    @staticmethod
    def ConfigHandler_set(key, value):
        ConfigHandler.cfg.put(key, value)
        return key, 'Plugins.ConfigHandler_get("' + str(key) + '")'

    @staticmethod
    def ConfigHandler_get(key):
        return ConfigHandler.cfg.get(key)

    @staticmethod
    def ConfigHandler_var(key="", value=""):
        if key != "" and value == "":
            output = Plugins.ConfigHandler_get(key)
        if key != "" and value != "":
            output = Plugins.ConfigHandler_set(key, value)
        return output

    @staticmethod
    def config_manual_generator(conf_dict):
        manual = ""
        for key, value in conf_dict.items():
            if key == "man":
                value = "manual for configuartion"
            if key == "micrOs_manual":
                value = "manual from microOs shell"
            try:
                value = str(eval(value))
            except Exception as e1:
                try:
                    value = str(exec(value))
                except Exception as e2:
                    interpreter_shell.server_console(str(value) + " is not a variable or function!\n" + str(e1) + "\n" + str(e2))
            key_lenght = len(str(key))
            manual += "config " + str(key) + " "*(20-key_lenght) + ": " + str(value) + "\n"
        return manual

#########################################################
#                                                       #
#                       DEMO AND TEST                   #
#                                                       #
#########################################################
try:
    if __name__ == "__main__":
        server = live_server(HOST, PORT, USER_TIMEOUT, UID, ID)
        server.run()
    if "live_server" in __name__:
        server = live_server(HOST, PORT, USER_TIMEOUT, UID, ID)
        server.run()
except KeyboardInterrupt:
        server.__del__()
