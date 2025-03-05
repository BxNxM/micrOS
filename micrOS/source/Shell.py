"""
Module is responsible for shell like environment
dedicated to micrOS framework.
Built-in-function:
- Shell wrapper for lm_exec interface
- Configuration handling interface - state machine handling
- Help (runtime) message generation

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                           IMPORTS                             #
#################################################################
from sys import modules
from uos import listdir
from machine import reset as hard_reset, soft_reset
from Config import cfgget, cfgput
from Tasks import lm_exec
from Debug import errlog_add


#################################################################
#                  SHELL Interpreter FUNCTIONS                  #
#################################################################

class Shell:
    __slots__ = ['__devfid', '__auth_mode', '__hwuid', '__auth_ok', '__conf_mode']
    MICROS_VERSION = '2.9.9-0'

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

    async def a_send(self, msg):
        """ Must be defined by child class... """
        raise NotImplementedError("Child class must implement a_send method")

    def reset(self):
        """Reset shell state"""
        self.__auth_ok = False
        self.__conf_mode = False

    async def reboot(self, hard=False):
        """ Reboot micropython VM """
        await self.a_send(f"{'[HARD] ' if hard else ''}Reboot micrOS system.\nBye!")
        if hard:
            hard_reset()
        soft_reset()

    def prompt(self):
        """ Generate prompt """
        auth = "[password] " if self.__auth_mode and not self.__auth_ok else ""
        mode = "[configure] " if self.__conf_mode else ""
        return f"{auth}{mode}{self.__devfid} $ "

    async def __auth(self, msg_list):
        """ Authorize user """
        # Set user auth state
        if self.__auth_mode and not self.__auth_ok:
            # check password
            usrpwd = cfgget('appwd')
            if usrpwd == msg_list[0].strip():
                self.__auth_ok = True
                await self.a_send("AuthOk")
                return True, []
            await self.a_send("AuthFailed\nBye!")
            return False, []
        return True, msg_list

    async def shell(self, msg):
        """
        micrOS Shell main - input string handling
        :param msg: incoming shell command (command or load module call)
        """
        state = await self.__shell(msg)
        await self.a_send(self.prompt())
        return state

    async def __shell(self, msg):
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
            await self.a_send(f"hello:{self.__devfid}:{self.__hwuid}")
            return True

        # [!] AUTH
        state, msg_list = await self.__auth(msg_list)
        if not state:
            return False
        if len(msg_list) == 0:
            return True

        # Version handling
        if msg_list[0] == 'version':
            # For micrOS system version info
            await self.a_send(str(Shell.MICROS_VERSION))
            return True

        # Reboot micropython VM
        if msg_list[0] == 'reboot':
            hard = False
            if len(msg_list) >= 2 and "-h" in msg_list[1]:
                # reboot / reboot -h
                hard = True
            await self.reboot(hard)

        if msg_list[0].startswith('webrepl'):
            if len(msg_list) == 2 and '-u' in msg_list[1]:
                await Shell.webrepl(msg_obj=self.a_send, update=True)
            return await Shell.webrepl(msg_obj=self.a_send)

        # CONFIGURE MODE STATE: ACCESS FOR NODE_CONFIG.JSON
        if msg_list[0].startswith('conf'):
            self.__conf_mode = True
            return True
        if msg_list[0].startswith('noconf'):
            self.__conf_mode = False
            return True

        # HELP MSG
        if msg_list[0] == "help":
            await self.a_send("[MICROS]   - built-in shell commands")
            await self.a_send("   hello   - hello msg - for device identification")
            await self.a_send("   modules - show active Load Modules")
            await self.a_send("   version - returns micrOS version")
            await self.a_send("   exit    - exit from shell socket prompt")
            await self.a_send("   reboot  - system soft reboot (vm), hard reboot (hw): reboot -h")
            await self.a_send("   webrepl - start webrepl, for file transfers use with --update")
            await self.a_send("[CONF] Configure mode - built-in shell commands")
            await self.a_send("  conf       - Enter conf mode")
            await self.a_send("    dump       - Dump all data")
            await self.a_send("    key        - Get value")
            await self.a_send("    key value  - Set value")
            await self.a_send("  noconf     - Exit conf mode")
            await self.a_send("[TASK] postfix: &x - one-time,  &&x - periodic, x: wait ms [x min: 20ms]")
            await self.a_send("  task list         - list tasks with <tag>s")
            await self.a_send("  task kill <tag>   - stop task")
            await self.a_send("  task show <tag>   - show task output")
            await self.a_send("[EXEC] Command mode (LMs):")
            await self.a_send("   help lm  - list ALL LoadModules")
            if "lm" in str(msg_list):
                return await Shell._show_lm_funcs(msg_obj=self.a_send)
            return await Shell._show_lm_funcs(msg_obj=self.a_send, active_only=True)

        # [2] EXECUTE:
        # @1 Configure mode
        if self.__conf_mode and len(msg_list) > 0:
            # Lock thread under config handling is threads available
            return await Shell._configure(self.a_send, msg_list)
        # @2 Command mode
        """
        INPUT MSG STRUCTURE
        1. param. - LM name, i.e. LM_commands
        2. param. - function call with parameters, i.e. a()
        """
        try:
            # Execute command via InterpreterCore
            await self.a_send(lm_exec(arg_list=msg_list)[1])
            return True
        except Exception as e:
            await self.a_send(f"[ERROR] shell.lm_exec internal error: {e}")
            return False

    #################################################################
    #                     CONFIGURE MODE HANDLER                    #
    #################################################################
    @staticmethod
    async def _configure(msg_obj, msg_list):
        """
        :param msg_obj: shell output stream function reference (write object)
        :param msg_list: socket input param list
        :return: execution status
        """
        async def dump():
            nonlocal msg_obj, msg_list
            if msg_list[0] == 'dump':
                search = msg_list[1] if len(msg_list) == 2 else None
                # DUMP DATA
                for _key, value in cfgget().items():
                    if search is None or search in _key:
                        await msg_obj(f"  {_key}{' ' * (10 - len(_key))}:{' ' * 7} {value}")
                return True
            return False

        # [CONFIG] Get value
        if len(msg_list) == 1:
            if await dump():                      # Simple dump without param filter
                return True
            # GET SINGLE PARAMETER VALUE
            await msg_obj(cfgget(msg_list[0]))
            return True
        # [CONFIG] Set value
        if len(msg_list) >= 2:
            if await dump():                      # Dump with search option
                return True
            # Deserialize params
            key = msg_list[0]
            # Set the parameter value in config
            try:
                output = cfgput(key, " ".join(msg_list[1:]), type_check=True)
            except Exception as e:
                await msg_obj(f"node_config write error: {e}")
                output = False
            # Evaluation and reply
            await msg_obj('Saved' if output else 'Invalid key' if cfgget(key) is None else 'Failed to save')
        return True

    #################################################################
    #                   COMMAND MODE & LMS HANDLER                  #
    #################################################################
    @staticmethod
    async def _show_lm_funcs(msg_obj, active_only=False):
        """
        Dump LM modules with functions - in case of [py] files
        Dump LM module with help function call - in case of [mpy] files
        """
        async def _help(mod):
            for lm_path in (i for i in mod if i.startswith('LM_') and (i.endswith('py'))):
                lm_name = lm_path.replace('LM_', '').split('.')[0]
                try:
                    await msg_obj(f"   {lm_name}")
                    if lm_path.endswith('.mpy'):
                        await msg_obj(f"   {' ' * len(lm_path.replace('LM_', '').split('.')[0])}help")
                        continue
                    with open(lm_path, 'r') as f:
                        line = "micrOSisTheBest"
                        while line:
                            line = f.readline()
                            ldata = line.strip()
                            if ldata.startswith('def ') and not ldata.split()[1].startswith("_") and 'self' not in ldata:
                                await msg_obj(f"   {' ' * len(lm_name)}{ldata.replace('def ', '').split('(')[0]}")
                except Exception as e:
                    await msg_obj(f"[{lm_path}] SHOW LM PARSER WARNING: {e}")
                    return False
            return True

        # [1] list active modules (default in shell)
        if active_only:
            mod_keys = modules.keys()
            active_modules = (dir_mod for dir_mod in listdir() if dir_mod.split('.')[0] in mod_keys)
            return await _help(active_modules)
        # [2] list all LMs on file system (ALL - help lm) - manual
        return await _help(listdir())

    @staticmethod
    async def webrepl(msg_obj, update=False):
        from Network import ifconfig

        await msg_obj(" Start micropython WEBREPL - file transfer and debugging")
        await msg_obj("  [i] restart machine shortcut: import reset")
        await msg_obj(f"  Connect over http://micropython.org/webrepl/#{ifconfig()[1][0]}:8266/")
        await msg_obj(f"  \t[!] webrepl password: {cfgget('appwd')}")
        if update:
            await msg_obj(" Restart node then start webrepl...")
            await msg_obj(" Bye!")
            # Set .if_mode->webrepl (start webrepl after reboot and poll update status...)
            with open('.if_mode', 'w') as f:
                f.write('webrepl')
            hard_reset()
        try:
            import webrepl
            await msg_obj(webrepl.start(password=cfgget('appwd')))
        except Exception as e:
            _err_msg = f"[ERR] while starting webrepl: {e}"
            await msg_obj(_err_msg)
            errlog_add(_err_msg)
        return True
