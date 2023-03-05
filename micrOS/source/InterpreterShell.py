"""
Module is responsible for shell like environment
dedicated to micrOS framework.
Built-in-function:
- Shell wrapper for safe InterpreterCore interface
- Configuration handling interface - state machine handling
- Help (runtime) message generation

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                           IMPORTS                             #
#################################################################
from os import listdir
from sys import modules
from ConfigHandler import cfgget, cfgput
from TaskManager import exec_lm_core
from Debug import console_write, errlog_add
from Network import ifconfig

try:
    from gc import collect, mem_free
except:
    from simgc import collect, mem_free  # simulator mode


#################################################################
#                  SHELL Interpreter FUNCTIONS                  #
#################################################################

class Shell:
    __socket_interpreter_version = '1.14.1-0'

    def __init__(self, msg_obj=None):
        """
        comm_obj - communication object - send messages back
                 - comm_obj.reply_message('msg')
        """
        self.msg_obj = msg_obj
        # Used node_config parameters
        self.__devfid = cfgget('devfid')
        self.__auth_mode = cfgget('auth')
        self.__hwuid = cfgget("hwuid")
        # State machine
        self.__auth_ok = False          # session authentication state (auth mode)
        self.__conf_mode = False        # session conf mode: on / off
        # Set proper micrOS version
        try:
            cfgput('version', Shell.__socket_interpreter_version)
        except Exception as e:
            console_write("Export system version to config failed: {}".format(e))
            errlog_add('[Shell.init][ERR] system version export error: {}'.format(e))

    def msg(self, msg):
        """Message stream method"""
        try:
            self.msg_obj(msg)
        except:
            print(msg)

    def reset(self):
        """Reset shell state"""
        self.__auth_ok = False
        self.__conf_mode = False

    def reboot(self, hard=False):
        """Reboot micropython VM"""
        self.msg("{}Reboot micrOS system.".format("[HARD] " if hard else ""))
        self.msg("Bye!")
        if hard:
            from machine import reset
            reset()
        from machine import soft_reset
        soft_reset()

    def prompt(self):
        """Generate prompt"""
        auth = "[password] " if self.__auth_mode and not self.__auth_ok else ""
        mode = "[configure] " if self.__conf_mode else ""
        return "{}{}{} $ ".format(auth, mode, self.__devfid)

    def __authentication(self, msg_list):
        """Authorize user"""
        # Set user auth state
        if self.__auth_mode and not self.__auth_ok:
            # check password
            usrpwd = cfgget('appwd')
            if usrpwd == msg_list[0].strip():
                self.__auth_ok = True
                self.msg("AuthOk")
                return True, []
            self.msg("AuthFailed\nBye!")
            return False, []
        return True, msg_list

    def shell(self, msg):
        state = self.__shell(msg)
        self.msg(self.prompt())
        return state

    def __shell(self, msg):
        """
        Socket server - interpreter shell
        :param msg: socket input string
        :return: execution status
            True: OK/HEALTHY
            False: ERROR/FAULTY -> actions
        """

        #################################
        #     [0] PARSE RAW STR MSG     #
        #################################
        if msg is None or len(msg.strip()) == 0:
            # No msg to work with
            return True
        msg_list = msg.strip().split()

        ##########################################
        #   [1] Handle built-in shell commands   #
        # hello, *auth, version, reboot, webrepl #
        ##########################################

        # Hello message
        if msg_list[0] == 'hello':
            # For low level device identification - hello msg
            self.msg("hello:{}:{}".format(self.__devfid, self.__hwuid))
            return True

        state, msg_list = self.__authentication(msg_list)
        if not state:
            return False
        if len(msg_list) == 0:
            return True

        # Version handling
        if msg_list[0] == 'version':
            # For micrOS system version info
            self.msg("{}".format(Shell.__socket_interpreter_version))
            return True

        # Reboot micropython VM
        if msg_list[0] == 'reboot':
            hard = False
            if len(msg_list) >= 2 and "-h" in msg_list[1]:
                # reboot / reboot -h
                hard = True
            self.reboot(hard)

        if msg_list[0].startswith('webrepl'):
            if len(msg_list) == 2 and '-u' in msg_list[1]:
                self.micropython_webrepl(update=True)
            self.micropython_webrepl()

        # CONFIGURE MODE STATE: ACCESS FOR NODE_CONFIG.JSON
        if msg_list[0].startswith('conf'):
            self.__conf_mode = True
            return True
        elif msg_list[0].startswith('noconf'):
            self.__conf_mode = False
            return True

        # HELP MSG
        if msg_list[0] == "help":
            self.msg("[MICROS]   - built-in shell commands")
            self.msg("   hello   - hello msg - for device identification")
            self.msg("   version - returns micrOS version")
            self.msg("   exit    - exit from shell socket prompt")
            self.msg("   reboot  - system soft reboot (vm), hard reboot (hw): reboot -h")
            self.msg("   webrepl - start webrepl, for file transfers use with --update")
            self.msg("[CONF] Configure mode - built-in shell commands")
            self.msg("  conf       - Enter conf mode")
            self.msg("    dump       - Dump all data")
            self.msg("    key        - Get value")
            self.msg("    key value  - Set value")
            self.msg("  noconf     - Exit conf mode")
            self.msg("[TASK] postfix: &x - one-time,  &&x - periodic, x: wait ms [x min: 20ms]")
            self.msg("  task list         - list tasks with <tag>s")
            self.msg("  task kill <tag>   - stop task")
            self.msg("  task show <tag>   - show task output")
            self.msg("[EXEC] Command mode (LMs):")
            self.msg("   help lm  - list ALL LoadModules")
            if "lm" in str(msg_list):
                return self.__show_LM_functions()
            return self.__show_LM_functions(active_only=True)

        # [2] EXECUTE:
        # @1 Configure mode
        if self.__conf_mode and len(msg_list) > 0:
            # Lock thread under config handling is threads available
            return self.__configure(msg_list)
        # @2 Command mode
        """
        INPUT MSG STRUCTURE
        1. param. - LM name, i.e. LM_commands
        2. param. - function call with parameters, i.e. a()
        """
        try:
            # Execute command via InterpreterCore
            return exec_lm_core(arg_list=msg_list, msgobj=self.msg)
        except Exception as e:
            self.msg("[ERROR] exec_lm_shell internal error: {}".format(e))
            return False

    #################################################################
    #                     CONFIGURE MODE HANDLER                    #
    #################################################################
    def __configure(self, attributes):
        """
        :param attributes: socket input param list
        :param sso: socket server object
        :return: execution status
        """
        # [CONFIG] Get value
        if len(attributes) == 1:
            if attributes[0] == 'dump':
                # DUMP DATA
                for key, value in cfgget().items():
                    spcr = (10 - len(key))
                    self.msg("  {}{}:{} {}".format(key, " " * spcr, " " * 7, value))
                return True
            # GET SINGLE PARAMETER VALUE
            self.msg(cfgget(attributes[0]))
            return True
        # [CONFIG] Set value
        if len(attributes) >= 2:
            # Deserialize params
            key = attributes[0]
            value = " ".join(attributes[1:])
            # Set the parameter value in config
            try:
                output = cfgput(key, value, type_check=True)
            except Exception as e:
                self.msg("node_config write error: {}".format(e))
                output = False
            # Evaluation and reply
            issue_msg = 'Invalid key' if cfgget(key) is None else 'Failed to save'
            self.msg('Saved' if output else issue_msg)
        return True

    #################################################################
    #                   COMMAND MODE & LMS HANDLER                  #
    #################################################################
    def __show_LM_functions(self, active_only=False):
        """
        Dump LM modules with functions - in case of [py] files
        Dump LM module with help function call - in case of [mpy] files
        """
        def _offline_help(module_list):
            for lm_path in (i for i in module_list if i.startswith('LM_') and (i.endswith('py'))):
                lm_name = lm_path.replace('LM_', '').split('.')[0]
                try:
                    self.msg("   {}".format(lm_name))
                    if lm_path.endswith('.mpy'):
                        self.msg("   {}help".format(" " * len(lm_path.replace('LM_', '').split('.')[0])))
                        continue
                    with open(lm_path, 'r') as f:
                        line = "micrOSisTheBest"
                        while line:
                            line = f.readline()
                            if line.strip().startswith('def') and '_' not in line and 'self' not in line:
                                self.msg("   {}{}".format(" " * len(lm_name), line.replace('def ', '').split('(')[0]))
                except Exception as e:
                    self.msg("[{}] SHOW LM PARSER WARNING: {}".format(lm_path, e))
                    return False
            return True

        # [1] list active modules (default in shell)
        if active_only:
            mod_keys = modules.keys()
            active_modules = (dir_mod for dir_mod in listdir() if dir_mod.split('.')[0] in mod_keys)
            return _offline_help(active_modules)
        # [2] list all LMs on file system (ALL - help lm) - manual
        return _offline_help(listdir())

    def micropython_webrepl(self, update=False):
        self.msg(" Start micropython WEBREPL for interpreter web access and file transferring.")
        self.msg("  [!] micrOS socket shell will be available again after reboot.")
        self.msg("  \trestart machine shortcut: import reset")
        self.msg("  Connect over http://micropython.org/webrepl/#{}:8266/".format(ifconfig()[1][0]))
        self.msg("  \t[!] webrepl password: {}".format(cfgget('appwd')))
        if update:
            self.msg('  Restart node then start webrepl...')
        self.msg(" Bye!")
        if update:
            from machine import reset
            with open('.if_mode', 'w') as f:
                f.write('webrepl')
            reset()
        try:
            import webrepl
            self.msg(webrepl.start(password=cfgget('appwd')))
        except Exception as e:
            self.msg("Error while starting webrepl: {}".format(e))
            errlog_add('[ERR] Start Webrepl error: {}'.format(e))
