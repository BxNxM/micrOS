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
from machine import reset as hard_reset, soft_reset
from Config import cfgget, cfgput
from Tasks import lm_exec
from Debug import errlog_add


#################################################################
#                  SHELL Interpreter FUNCTIONS                  #
#################################################################

class Shell:
    MICROS_VERSION = '2.4.0-0'

    def __init__(self):
        """
        Shell class for prompt based communication
        - send method have to be defined by child class -> SocektServer.send !!!
        """
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
            errlog_add(f"[ERR] micrOS version export failed (config): {e}")

    def send(self, msg):
        """
        Must be defined by child class...
        """
        pass

    def reset(self):
        """Reset shell state"""
        self.__auth_ok = False
        self.__conf_mode = False

    def reboot(self, hard=False):
        """Reboot micropython VM"""
        self.send(f"{'[HARD] ' if hard else ''}Reboot micrOS system.")
        self.send("Bye!")
        if hard:
            hard_reset()
        soft_reset()

    def prompt(self):
        """Generate prompt"""
        auth = "[password] " if self.__auth_mode and not self.__auth_ok else ""
        mode = "[configure] " if self.__conf_mode else ""
        return f"{auth}{mode}{self.__devfid} $ "

    def __auth(self, msg_list):
        """Authorize user"""
        # Set user auth state
        if self.__auth_mode and not self.__auth_ok:
            # check password
            usrpwd = cfgget('appwd')
            if usrpwd == msg_list[0].strip():
                self.__auth_ok = True
                self.send("AuthOk")
                return True, []
            self.send("AuthFailed\nBye!")
            return False, []
        return True, msg_list

    def shell(self, msg):
        """
        micrOS Shell main - input string handling
        :param msg: incoming shell command (command or load module call)
        """
        state = self.__shell(msg)
        self.send(self.prompt())
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
            self.send(f"hello:{self.__devfid}:{self.__hwuid}")
            return True

        # [!] AUTH
        state, msg_list = self.__auth(msg_list)
        if not state:
            return False
        if len(msg_list) == 0:
            return True

        # Version handling
        if msg_list[0] == 'version':
            # For micrOS system version info
            self.send(str(Shell.MICROS_VERSION))
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
                Shell.webrepl(msg_obj=self.send, update=True)
            Shell.webrepl(msg_obj=self.send)

        # CONFIGURE MODE STATE: ACCESS FOR NODE_CONFIG.JSON
        if msg_list[0].startswith('conf'):
            self.__conf_mode = True
            return True
        if msg_list[0].startswith('noconf'):
            self.__conf_mode = False
            return True

        # HELP MSG
        if msg_list[0] == "help":
            self.send("[MICROS]   - built-in shell commands")
            self.send("   hello   - hello msg - for device identification")
            self.send("   modules - show active Load Modules")
            self.send("   version - returns micrOS version")
            self.send("   exit    - exit from shell socket prompt")
            self.send("   reboot  - system soft reboot (vm), hard reboot (hw): reboot -h")
            self.send("   webrepl - start webrepl, for file transfers use with --update")
            self.send("[CONF] Configure mode - built-in shell commands")
            self.send("  conf       - Enter conf mode")
            self.send("    dump       - Dump all data")
            self.send("    key        - Get value")
            self.send("    key value  - Set value")
            self.send("  noconf     - Exit conf mode")
            self.send("[TASK] postfix: &x - one-time,  &&x - periodic, x: wait ms [x min: 20ms]")
            self.send("  task list         - list tasks with <tag>s")
            self.send("  task kill <tag>   - stop task")
            self.send("  task show <tag>   - show task output")
            self.send("[EXEC] Command mode (LMs):")
            self.send("   help lm  - list ALL LoadModules")
            if "lm" in str(msg_list):
                return Shell._show_lm_funcs(msg_obj=self.send)
            return Shell._show_lm_funcs(msg_obj=self.send, active_only=True)

        # [2] EXECUTE:
        # @1 Configure mode
        if self.__conf_mode and len(msg_list) > 0:
            # Lock thread under config handling is threads available
            return Shell._configure(self.send, msg_list)
        # @2 Command mode
        """
        INPUT MSG STRUCTURE
        1. param. - LM name, i.e. LM_commands
        2. param. - function call with parameters, i.e. a()
        """
        try:
            # Execute command via InterpreterCore
            self.send(lm_exec(arg_list=msg_list)[1])
            return True
        except Exception as e:
            self.send(f"[ERROR] shell.lm_exec internal error: {e}")
            return False

    #################################################################
    #                     CONFIGURE MODE HANDLER                    #
    #################################################################
    @staticmethod
    def _configure(msg_obj, msg_list):
        """
        :param msg_obj: shell output stream function reference (write object)
        :param msg_list: socket input param list
        :return: execution status
        """
        def dump():
            nonlocal msg_obj, msg_list
            if msg_list[0] == 'dump':
                search = msg_list[1] if len(msg_list) == 2 else None
                # DUMP DATA
                for _key, value in cfgget().items():
                    if search is None or search in _key:
                        msg_obj(f"  {_key}{' ' * (10 - len(_key))}:{' ' * 7} {value}")
                return True
            return False

        # [CONFIG] Get value
        if len(msg_list) == 1:
            if dump():                      # Simple dump without param filter
                return True
            # GET SINGLE PARAMETER VALUE
            msg_obj(cfgget(msg_list[0]))
            return True
        # [CONFIG] Set value
        if len(msg_list) >= 2:
            if dump():                      # Dump with search option
                return True
            # Deserialize params
            key = msg_list[0]
            # Set the parameter value in config
            try:
                output = cfgput(key, " ".join(msg_list[1:]), type_check=True)
            except Exception as e:
                msg_obj(f"node_config write error: {e}")
                output = False
            # Evaluation and reply
            msg_obj('Saved' if output else 'Invalid key' if cfgget(key) is None else 'Failed to save')
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
        def _help(mod):
            for lm_path in (i for i in mod if i.startswith('LM_') and (i.endswith('py'))):
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
            return _help(active_modules)
        # [2] list all LMs on file system (ALL - help lm) - manual
        return _help(listdir())

    @staticmethod
    def webrepl(msg_obj, update=False):
        from Network import ifconfig

        msg_obj(" Start micropython WEBREPL - file transfer and debugging")
        msg_obj("  [i] restart machine shortcut: import reset")
        msg_obj(f"  Connect over http://micropython.org/webrepl/#{ifconfig()[1][0]}:8266/")
        msg_obj(f"  \t[!] webrepl password: {cfgget('appwd')}")
        if update:
            msg_obj(" Restart node then start webrepl...")
            msg_obj(" Bye!")
            # Set .if_mode->webrepl (start webrepl after reboot and poll update status...)
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
