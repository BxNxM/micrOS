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
from ConfigHandler import cfgget, cfgput, cfgget_all
from InterpreterCore import execute_LM_function_Core


#################################################################
#                  SHELL Interpreter FUNCTIONS                  #
#################################################################


def shell(msg, SocketServerObj):
    """
    Socket server - interpreter shell wrapper
    return state:
        True - OK, no actions
        False - ISSUE, recovery actions triggered in upper logic
    """
    try:
        state = __shell(msg, SocketServerObj)
        return state
    except Exception as e:
        SocketServerObj.reply_message("[SHELL] Runtime error: {}".format(e))
        return False


def __shell(msg, SocketServerObj):
    """
    Socket server - interpreter shell
    RETURN STATE:
        True: OK/HEALTHY
        False: ERROR/FAULTY
    """

    # PARSE RAW STR MSG
    if msg is None or len(msg.strip()) == 0:
        # No msg to work with
        return True
    msg_list = msg.strip().split()

    # CONFIGURE MODE STATE: ACCESS FOR NODE_CONFIG.JSON
    if msg_list[0] == "configure" or msg_list[0] == "conf":
        SocketServerObj.CONFIGURE_MODE = True
        SocketServerObj.pre_prompt = "[configure] "
        return True
    elif msg_list[0] == "noconfigure" or msg_list[0] == "noconf":
        SocketServerObj.CONFIGURE_MODE = False
        SocketServerObj.pre_prompt = ""
        return True

    # HELP MSG
    if msg_list[0] == 'help':
        SocketServerObj.reply_message("[MICROS]   - commands (built-in)")
        SocketServerObj.reply_message("   hello   - default hello msg - identify device (SocketServer)")
        SocketServerObj.reply_message("   version - shows MicrOS version")
        SocketServerObj.reply_message("   exit    - exit from shell socket prompt (SocketServer)")
        SocketServerObj.reply_message("   webrepl - start web repl for file transfers - update")
        SocketServerObj.reply_message("   reboot  - system safe reboot (SocketServer)")
        SocketServerObj.reply_message("[CONF] Configure mode (built-in):")
        SocketServerObj.reply_message("   configure|conf     - Enter conf mode")
        SocketServerObj.reply_message("         Key          - Get value")
        SocketServerObj.reply_message("         Key:Value    - Set value")
        SocketServerObj.reply_message("         dump         - Dump all data")
        SocketServerObj.reply_message("   noconfigure|noconf - Exit conf mod")
        SocketServerObj.reply_message("[EXEC] Command mode (LMs):")
        show_LMs_functions(SocketServerObj)
        return True

    # EXECUTE:
    # @1 Configure mode
    if SocketServerObj.CONFIGURE_MODE and len(msg_list) != 0:
        return configure(msg_list, SocketServerObj)
    # @2 Command mode
    elif not SocketServerObj.CONFIGURE_MODE and len(msg_list) != 0:
        """
        INPUT MSG STRUCTURE
        1. param. - LM name, i.e. LM_commands
        2. param. - function call with parameters, i.e. a()
        """
        try:
            # Execute command via InterpreterCore
            return execute_LM_function_Core(argument_list=msg_list, SocketServerObj=SocketServerObj)
        except Exception as e:
            SocketServerObj.reply_message("[ERROR] execute_LM_function_Core \
                                          internal error: {}".format(e))
            return False


#################################################################
#                     CONFIGURE MODE HANDLER                    #
#################################################################


def configure(attributes, SocketServerObj):
    # [CONFIG] Get value
    if len(attributes) == 1:
        if attributes[0] == "dump":
            # DUMP DATA
            for key, value in cfgget_all().items():
                spcr = (int(10 / 3) - int(10 / 5))
                spcr2 = (10 - len(key))
                SocketServerObj.reply_message("  {}{}:{} {}".format(key, " " * spcr2, " " * spcr, value))
        else:
            # GET SINGLE PARAMETER VALUE
            SocketServerObj.reply_message(cfgget(attributes[0]))
        return True
    # [CONFIG] Set value
    if len(attributes) >= 2:
        key = attributes[0]
        value = " ".join(attributes[1:])
        try:
            output = cfgput(key, value, type_check=True)
        except Exception as e:
            SocketServerObj.reply_message("node_config write error: {}".format(e))
            output = False
        SocketServerObj.reply_message('Saved' if output else 'Failed to save')
    return True


#################################################################
#                   COMMAND MODE & LMS HANDLER                  #
#################################################################


def show_LMs_functions(SocketServerObj):
    """
    Dump LM modules with functions - in case of [py] files
    Dump LM module with help function call - in case of [mpy] files
    """
    for LM in (i.split('.')[0] for i in listdir()
               if i.startswith('LM_') and (i.endswith('.py') or i.endswith('.mpy'))):
        LMpath = '{}.py'.format(LM)
        if LMpath not in listdir():
            LMpath = '{}.mpy'.format(LM)
        try:
            SocketServerObj.reply_message("   {}".format(LM.replace('LM_', '')))
            if LMpath.endswith('.mpy'):
                SocketServerObj.reply_message("   {}help".format(" " * len(LM.replace('LM_', ''))))
            else:
                with open(LMpath, 'r') as f:
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        if "def" in line and "def __" not in line:
                            SocketServerObj.reply_message("   {}{}"
                                                          .format(" " * len(LM.replace('LM_', '')),
                                                                  line.split('(')[0].split(' ')[1]))
        except Exception as e:
            SocketServerObj.reply_message("LM [{}] PARSER WARNING: {}".format(LM, e))
            raise Exception("show_LMs_functions [{}] exception: {}".format(LM, e))
