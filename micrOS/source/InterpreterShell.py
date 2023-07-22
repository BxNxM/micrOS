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
from machine import reset as hard_reset, soft_reset


#################################################################
#                  SHELL Interpreter FUNCTIONS                  #
#################################################################

class Shell:
    MICROS_VERSION = '1.20.4-0'

    def __init__(self, msg_obj=None):
        """
        comm_obj - communication object - send messages back
                 - comm_obj.reply('msg')
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
            cfgput('version', Shell.MICROS_VERSION)
        except Exception as e:
            console_write(f"Export system version to config failed: {e}")
            errlog_add(f"[Shell][ERR] system version export error: {e}")

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
        self.msg(f"{'[HARD] ' if hard else ''}Reboot micrOS system.")
        self.msg("Bye!")
        if hard:
            hard_reset()
        soft_reset()

    def prompt(self):
        """Generate prompt"""
        auth = "[password] " if self.__auth_mode and not self.__auth_ok else ""
        mode = "[configure] " if self.__conf_mode else ""
        return f"{auth}{mode}{self.__devfid} $ "

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
        """
        micrOS Shell main - input string handling
        :param msg: incoming shell command (command or load module call)
        """
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
            self.msg(f"hello:{self.__devfid}:{self.__hwuid}")
            return True

        state, msg_list = self.__authentication(msg_list)
        if not state:
            return False
        if len(msg_list) == 0:
            return True

        # Version handling
        if msg_list[0] == 'version':
            # For micrOS system version info
            self.msg(str(Shell.MICROS_VERSION))
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
                Shell.webrepl(msg_obj=self.msg, update=True)
            Shell.webrepl(msg_obj=self.msg)

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
                return Shell._show_lm_funcs(msg_obj=self.msg)
            return Shell._show_lm_funcs(msg_obj=self.msg, active_only=True)

        # [2] EXECUTE:
        # @1 Configure mode
        if self.__conf_mode and len(msg_list) > 0:
            # Lock thread under config handling is threads available
            return Shell._configure(self.msg, msg_list)
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
            self.msg(f"[ERROR] exec_lm_shell internal error: {e}")
            return False

    #################################################################
    #                     CONFIGURE MODE HANDLER                    #
    #################################################################
    @staticmethod
    def _configure(msg_obj, attributes):
        """
        :param msg_obj: shell output stream function pointer (write object)
        :param attributes: socket input param list
        :return: execution status
        """
        # [CONFIG] Get value
        if len(attributes) == 1:
            if attributes[0] == 'dump':
                # DUMP DATA
                for key, value in cfgget().items():
                    spcr = (10 - len(key))
                    msg_obj(f"  {key}{' ' * spcr}:{' ' * 7} {value}")
                return True
            # GET SINGLE PARAMETER VALUE
            msg_obj(cfgget(attributes[0]))
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
                msg_obj(f"node_config write error: {e}")
                output = False
            # Evaluation and reply
            issue_msg = 'Invalid key' if cfgget(key) is None else 'Failed to save'
            msg_obj('Saved' if output else issue_msg)
        return True

    #################################################################
    #                   COMMAND MODE & LMS HANDLER                  #
    #################################################################
    @staticmethod
    def _show_lm_funcs(msg_obj, active_only=False):
        """
        Dump LM modules with functions - in case of [py] files
        Dump LM module with help function call - in case of [mpy] files
        """
        def _offline_help(module_list):
            for lm_path in (i for i in module_list if i.startswith('LM_') and (i.endswith('py'))):
                lm_name = lm_path.replace('LM_', '').split('.')[0]
                try:
                    msg_obj(f"   {lm_name}")
                    if lm_path.endswith('.mpy'):
                        msg_obj(f"   {' ' * len(lm_path.replace('LM_', '').split('.')[0])}help")
                        continue
                    with open(lm_path, 'r') as f:
                        line = "micrOSisTheBest"
                        while line:
                            line = f.readline()
                            if line.strip().startswith('def') and '_' not in line and 'self' not in line:
                                msg_obj(f"   {' ' * len(lm_name)}{line.replace('def ', '').split('(')[0]}")
                except Exception as e:
                    msg_obj(f"[{lm_path}] SHOW LM PARSER WARNING: {e}")
                    return False
            return True

        # [1] list active modules (default in shell)
        if active_only:
            mod_keys = modules.keys()
            active_modules = (dir_mod for dir_mod in listdir() if dir_mod.split('.')[0] in mod_keys)
            return _offline_help(active_modules)
        # [2] list all LMs on file system (ALL - help lm) - manual
        return _offline_help(listdir())

    @staticmethod
    def webrepl(msg_obj, update=False):
        from Network import ifconfig

        msg_obj(" Start micropython WEBREPL - file transfer and debugging")
        msg_obj("  [i] restart machine shortcut: import reset")
        msg_obj(f"  Connect over http://micropython.org/webrepl/#{ifconfig()[1][0]}:8266/")
        msg_obj(f"  \t[!] webrepl password: {cfgget('appwd')}")
        if update:
            msg_obj('  Restart node then start webrepl...')
        msg_obj(" Bye!")
        if update:
            # Set update poller by interface mode file: .if_mode
            with open('.if_mode', 'w') as f:
                f.write('webrepl')
            hard_reset()
        try:
            import webrepl
            msg_obj(webrepl.start(password=cfgget('appwd')))
        except Exception as e:
            _err_msg = f"[ERR] while starting webrepl: {e}"
            msg_obj(_err_msg)
            errlog_add(_err_msg)
