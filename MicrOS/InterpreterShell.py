try:
    from ConfigHandler import cfgget, cfgput, cfgget_all
except Exception as e:
    print("Failed to import ConfigHandler: {}".format(e))

try:
    from machine import disable_irq, enable_irq
except Exception as e:
    disable_irq = None
    enable_irq = None
    print("Failed to import machine: {}".format(e))

from os import listdir
from sys import modules

#########################################################
#             SHELL Interpreter FUNCTIONS               #
#########################################################


def shell(msg, SocketServerObj):
    '''
    Socket server - interpreter shell wrapper
    '''
    try:
        state = __shell(msg, SocketServerObj)
        return state, 'Okay'                   # True - good, False execute soft reboot
    except Exception as e:
        SocketServerObj.reply_message("[SHELL] Runtime error: {}".format(e))
        return False, str(e)


def __shell(msg, SocketServerObj):
    '''
    Socket server - interpreter shell
    '''
    retval = True

    if msg is None or len(msg.strip()) == 0:
        return retval
    msg_list = msg.strip().split()

    # CONFIGURE MODE 'ENV' SETUP
    if msg_list[0] == "configure" or msg_list[0] == "conf":
        if len(msg_list) == 1:
            SocketServerObj.CONFIGURE_MODE = True
            SocketServerObj.pre_prompt = "[configure] "
        msg_list = []
    elif msg_list[0] == "noconfigure" or msg_list[0] == "noconf":
        if len(msg_list) == 1:
            SocketServerObj.CONFIGURE_MODE = False
            SocketServerObj.pre_prompt = ""
        msg_list = []

    # HELP MSG
    if "help" in msg_list and "help" == msg_list[0]:
        SocketServerObj.reply_message("hello   - default hello msg - identify device (SocketServer)")
        SocketServerObj.reply_message("version - shows MicrOS version")
        SocketServerObj.reply_message("exit    - exit from shell socket prompt (SocketServer)")
        SocketServerObj.reply_message("reboot  - system safe reboot (SocketServer)")
        SocketServerObj.reply_message("[CONF] Configure mode:")
        SocketServerObj.reply_message("   configure|conf     - Enter conf mode")
        SocketServerObj.reply_message("         Key          - Get value")
        SocketServerObj.reply_message("         Key:Value    - Set value")
        SocketServerObj.reply_message("         dump         - Dump all data")
        SocketServerObj.reply_message("   noconfigure|noconf - Exit conf mod")
        SocketServerObj.reply_message("[EXEC] Command mode:")
        show_LMs_functions(SocketServerObj)
        msg_list = []

    # EXECUTE:
    # @1 Configure mode
    if SocketServerObj.CONFIGURE_MODE and len(msg_list) != 0:
        retval = configure(msg_list, SocketServerObj)
    # @2 Command mode
    elif not SocketServerObj.CONFIGURE_MODE and len(msg_list) != 0:
        retval = execute_LM_function(argument_list=msg_list, SocketServerObj=SocketServerObj)

    return retval

#########################################################
#               CONFIGURE MODE HANDLER                  #
#########################################################


def configure(attributes, SocketServerObj):
    # DISBALE BG INTERRUPTS
    if disable_irq is not None:
        status = disable_irq()
    # [CONFIG] Get value
    if len(attributes) == 1:
        if attributes[0] == "dump":
            val_spacer = 10
            for key, value in cfgget_all().items():
                spcr = (int(val_spacer/3) - int(val_spacer/5))
                spcr2 = (val_spacer - len(key))
                SocketServerObj.reply_message("  {}{}:{} {}".format(key, " "*spcr2, " "*spcr,  value))
        else:
            key = attributes[0]
            SocketServerObj.reply_message(cfgget(key))
    # [CONFIG] Set value
    elif len(attributes) >= 2:
        key = attributes[0]
        value = " ".join(attributes[1:])
        try:
            SocketServerObj.reply_message(cfgput(key, value))
        except Exception as e:
            SocketServerObj.reply_message("Set config error: ".format(e))
    # ENABLE BG INTERRUPTS
    if enable_irq is not None:
        enable_irq(status)
    return True

#########################################################
#               COMMAND MODE & LMS HANDLER              #
#########################################################


def show_LMs_functions(SocketServerObj):
    for LM in [i.split('.')[0] for i in listdir() if i.startswith('LM_') and (i.endswith('.py') or i.endswith('.mpy'))]:
        LMpath = '{}.py'.format(LM)
        if LMpath not in listdir():
            LMpath = '{}.mpy'.format(LM)
        try:
            SocketServerObj.reply_message("   {}".format(LM.replace('LM_', '')))
            if LMpath.endswith('.mpy'):
                SocketServerObj.reply_message("   {}help".format(" "*len(LM.replace('LM_', ''))))
            else:
                with open(LMpath, 'r') as f:
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        if "def" in line and "def __" not in line:
                            SocketServerObj.reply_message("   {}{}".format(" "*len(LM.replace('LM_', '')), line.split('(')[0].split(' ')[1]))
        except Exception as e:
            SocketServerObj.reply_message("LM [{}] PARSER WARNING: {}".format(LM, e))
            raise Exception("show_LMs_functions [{}] exception: {}".format(LM, e))


def execute_LM_function_Core(argument_list, SocketServerObj=None):
    '''
    1. param. - LM name, i.e. LM_commands
    2. param. - function call with parameters, i.e. a()
    NOTE: SocketServerObj is None from Interrupts and Hooks - shared functionality
    '''
    recovery_query = False
    if len(argument_list) >= 2:
        LM_name = "LM_{}".format(argument_list[0])
        LM_function_call = "".join(argument_list[1:])
        LM_function = argument_list[1].split('(')[0]
        if "(" not in LM_function_call and ")" not in LM_function_call:
            LM_function_call = "{}()".format(LM_function)
    try:
        # --- LM LOAD & EXECUTE --- #
        if SocketServerObj is not None:
            SocketServerObj.server_console("from {} import {}".format(LM_name, LM_function))
        # [1] LOAD MODULE
        exec("from {} import {}".format(LM_name, LM_function))
        # [2] EXECUTE FUNCTION FROM MODULE
        if SocketServerObj is not None:
            SocketServerObj.reply_message(str(eval("{}".format(LM_function_call))))
        else:
            eval("{}".format(LM_function_call))
        # ------------------------- #
    except Exception as e:
        if SocketServerObj is not None:
            SocketServerObj.reply_message("execute_LM_function {}->{}: {}".format(LM_name, LM_function, e))
        else:
            print("execute_LM_function {}->{}: {}".format(LM_name, LM_function, e))
        if "memory allocation failed" in str(e):
            # UNLOAD MODULE IF MEMORY ERROR ACCURED
            if LM_name in modules.keys():
                del modules[LM_name]
            recovery_query = True
    # RETURN WITH HEALTH STATE - TRUE :) -> NO ACTION -or- FALSE :( -> RECOVERY ACTION
    return not recovery_query

def execute_LM_function(argument_list, SocketServerObj=None):
    '''
    1. param. - LM name, i.e. LM_commands
    2. param. - function call with parameters, i.e. a()
    '''
    try:
        if disable_irq is not None:
            status = disable_irq()
        health = execute_LM_function_Core(argument_list, SocketServerObj)
        if enable_irq is not None:
            enable_irq(status)
    except Exception as e:
        if enable_irq is not None:
            enable_irq(status)
        health = False
    # RETURN WITH HEALTH STATE - TRUE :) -> NO ACTION -or- FALSE :( -> RECOVERY ACTION
    return health

