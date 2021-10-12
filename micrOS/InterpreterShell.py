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
from ConfigHandler import cfgget, cfgput
from InterpreterCore import execLMCore
try:
    from BgJob import BgTask
except:
    BgTask = None

try:
    from gc import collect, mem_free
except:
    from simgc import collect, mem_free  # simulator mode


#################################################################
#                  SHELL Interpreter FUNCTIONS                  #
#################################################################

def shell(msg, sso):
    """
    Main micrOS socket shell wrapper
    :param msg: socket input string
    :param sso: socket server object
    :return: execution status
    """
    try:
        return __shell(msg, sso)
    except Exception as e:
        sso.reply_message("[SHELL] Runtime error: {}".format(e))
        return False


def __shell(msg, sso):
    """
    Socket server - interpreter shell
    :param msg: socket input string
    :param sso: socket server object
        Used stateful parameters:
            sso.configure_mode
            sso.pre_prompt
        Socket message method:
            sso.reply_message(<input string>)
    :return: execution status
        True: OK/HEALTHY
        False: ERROR/FAULTY
    """

    # PARSE RAW STR MSG
    if msg is None or len(msg.strip()) == 0:
        # No msg to work with
        return True
    msg_list = msg.strip().split()

    # CONFIGURE MODE STATE: ACCESS FOR NODE_CONFIG.JSON
    if msg_list[0].startswith('conf'):
        sso.configure_mode = True
        sso.pre_prompt = "[configure] "
        return True
    elif msg_list[0].startswith('noconf'):
        sso.configure_mode = False
        sso.pre_prompt = ""
        return True

    # HELP MSG
    if msg_list[0] == 'help':
        sso.reply_message("[MICROS]   - commands (SocketServer built-in)")
        sso.reply_message("   hello   - default hello msg - identify device")
        sso.reply_message("   version - shows micrOS version")
        sso.reply_message("   exit    - exit from shell socket prompt")
        sso.reply_message("   reboot  - system safe reboot")
        sso.reply_message("   webrepl - start web repl, use with --update for file transfers")
        sso.reply_message("[CONF] Configure mode (InterpreterShell built-in):")
        sso.reply_message("  conf       - Enter conf mode")
        sso.reply_message("    dump       - Dump all data")
        sso.reply_message("    key        - Get value")
        sso.reply_message("    key value  - Set value")
        sso.reply_message("  noconf     - Exit conf mode")
        sso.reply_message("[BGJOB] Background LM execution")
        sso.reply_message("    show     - Show running job data")
        sso.reply_message("    stop     - Stop running job")
        sso.reply_message("[EXEC] Command mode (LMs):")
        return __show_LM_functions(sso)

    # EXECUTE:
    # @1 Configure mode
    if sso.configure_mode and len(msg_list) > 0:
        # Config handling without thread locking
        if BgTask is None:
            return __configure(msg_list, sso)
        # Lock thread under config handling is threads available
        with BgTask.singleton():
            s = __configure(msg_list, sso)
        return s
    # @2 Background job shell commands
    if msg_list[0] == 'bgjob' and len(msg_list) > 1:
        if BgTask.singleton() is None:
            sso.reply_message('[BgJob] Inactive...')
            return True
        if msg_list[1] == 'stop':
            sso.reply_message(BgTask.singleton().stop())
            return True
        if msg_list[1] == 'show':
            sso.reply_message(BgTask.singleton().info())
            return True
    # @3 Command mode
    """
    INPUT MSG STRUCTURE
    1. param. - LM name, i.e. LM_commands
    2. param. - function call with parameters, i.e. a()
    """
    try:
        # Execute command via InterpreterCore
        return execLMCore(argument_list=msg_list, msgobj=sso.reply_message)
    except Exception as e:
        sso.reply_message("[ERROR] execLMCore internal error: {}".format(e))
        return False

#################################################################
#                     CONFIGURE MODE HANDLER                    #
#################################################################


def __configure(attributes, sso):
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
                sso.reply_message("  {}{}:{} {}".format(key, " " * spcr, " " * 7, value))
            return True
        # GET SINGLE PARAMETER VALUE
        sso.reply_message(cfgget(attributes[0]))
        return True
    # [CONFIG] Set value
    if len(attributes) >= 2:
        # Deserialize params
        key = attributes[0]
        value = " ".join(attributes[1:])
        # Check irq required memory
        if attributes[1].lower() == 'true':
            isOK, avmem = __irq_mem_req_check(key)
            if not isOK:
                sso.reply_message("Skip ... feature requires more memory then {} byte".format(avmem))
                return True
        # Set the parameter value in config
        try:
            output = cfgput(key, value, type_check=True)
        except Exception as e:
            sso.reply_message("node_config write error: {}".format(e))
            output = False
        # Evaluation and reply
        issue_msg = 'Invalid key' if cfgget(key) is None else 'Failed to save'
        sso.reply_message('Saved' if output else issue_msg)
    return True


def __irq_mem_req_check(key):
    """
    :param key: config param key to check
        Checks the selected config function hw resource need before setup
    :return: Enable(True)/Disable(False), available memory
    """
    if key not in ('timirq', 'irq1', 'irq2', 'irq3', 'irq14', 'cron'):
        return True, None
    collect()                   # gc collect
    memavail = mem_free()       # get free memory
    if key == 'timirq' and memavail < cfgget('irqmreq'):
        return False, memavail
    if key == 'cron' and memavail < cfgget('irqmreq') * 2:
        return False, memavail
    if key in ('irq1', 'irq2', 'irq3', 'irq4') and memavail < int(cfgget('irqmreq') * 0.7):
        return False, memavail
    return True, memavail


#################################################################
#                   COMMAND MODE & LMS HANDLER                  #
#################################################################


def __show_LM_functions(sso):
    """
    Dump LM modules with functions - in case of [py] files
    Dump LM module with help function call - in case of [mpy] files
    """
    for lm_path in (i for i in listdir() if i.startswith('LM_') and (i.endswith('py'))):
        lm_name = lm_path.replace('LM_', '').split('.')[0]
        try:
            sso.reply_message("   {}".format(lm_name))
            if lm_path.endswith('.mpy'):
                sso.reply_message("   {}help".format(" " * len(lm_path.replace('LM_', '').split('.')[0])))
                continue
            with open(lm_path, 'r') as f:
                line = "micrOSisTheBest"
                while line:
                    line = f.readline()
                    if line.strip().startswith('def') and '__' not in line and 'self' not in line:
                        sso.reply_message("   {}{}".format(" " * len(lm_name),
                                                                       line.replace('def ', '').split('(')[0]))
        except Exception as e:
            sso.reply_message("[{}] SHOW LM PARSER WARNING: {}".format(lm_path, e))
            return False
    return True
