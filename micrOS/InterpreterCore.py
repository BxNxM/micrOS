"""
Module is responsible for user executables invocation
dedicated to micrOS framework.
- Core element for socket based command (LM) handling
Used in:
- InterpreterShell
- InterruptHandler
- Hooks

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                           IMPORTS                             #
#################################################################
from sys import modules
from ConfigHandler import console_write
try:
    from BgJob import BgTask
except Exception as e:
    console_write('BgJob - thread support failed: {}'.format(e))
    BgTask = None

#################################################################
#               Interpreter shell CORE executor                 #
#################################################################


def startBgJob(argument_list, msg):
    # Handle Thread &/&& arguments [-1]
    is_thrd = argument_list[-1].strip()
    # Run OneShot job by default
    loop = False
    if '&' in is_thrd:
        if BgTask is None:
            msg('[BgJob] Inactive...')
            return True
        # delete from argument list - handled argument ...
        del argument_list[-1]
        # Get thread wait
        wait = int(is_thrd.replace('&', '')) if is_thrd.replace('&', '').isdigit() else 0
        # Create callback
        callback = lambda tmsg: __exec_lm_core(argument_list, msgobj=tmsg)
        if is_thrd.startswith('&&'):
            # Run task in background loop with custom sleep in period &&X
            loop = True
        # Start background thread based on user input
        stat, tid = BgTask().run(callback=callback, loop=loop, delay=wait)
        if stat:
            msg("[BgJob][{}] Start loop:{} successful".format(tid, loop))
            return True
        msg("[BgJob][{}] Busy".format(tid))
        return True
    return False


def execLMPipe(taskstr):
    """
    Input: taskstr contains LM calls separated by ;
    """
    ok = True
    try:
        # Handle config default empty value (do nothing)
        if taskstr.startswith('n/a'):
            return True
        # Execute individual commands
        for cmd in (cmd.strip().split() for cmd in taskstr.split(';')):
            if not execLMCore(cmd):
                console_write("|-[LM-PIPE] task error: {}".format(cmd))
                ok = False
    except Exception as e:
        console_write("[LM-PIPE] pipe error: {}\n{}".format(taskstr, e))
        return False
    return ok


def __exec_lm_core(argument_list, msgobj=None):
    """
    [1] module name (LM)
    [2] function
    [3...] parameters (separator: space)
    NOTE: msgobj is None from Interrupts and Hooks - shared functionality
    """
    # Check json mode for LM execution
    json_mode = argument_list[-1] == '>json'
    if json_mode:
        del argument_list[-1]
    # LoadModule execution
    if len(argument_list) >= 2:
        LM_name, LM_function, LM_function_params = "LM_{}".format(argument_list[0]), argument_list[1], ', '.join(argument_list[2:])
        try:
            # --- LM LOAD & EXECUTE --- #
            # [1] LOAD MODULE
            exec("import {}".format(LM_name))
            # [2] EXECUTE FUNCTION FROM MODULE - over msgobj (socket or stdout)
            lm_output = eval("{}.{}({})".format(LM_name, LM_function, LM_function_params))
            # Handle output data stream
            if not json_mode and isinstance(lm_output, dict):
                # Format dict output - human readable
                lm_output = '\n'.join(["{}: {}".format(key, value) for key, value in lm_output.items()])
                msgobj(str(lm_output))
            else:
                # Raw output if json
                msgobj(str(lm_output))
            # ------------------------- #
        except Exception as e:
            msgobj("execute_LM_function {}->{}: {}".format(LM_name, LM_function, e))
            if 'memory allocation failed' in str(e) or 'is not defined' in str(e):
                # UNLOAD MODULE IF MEMORY ERROR HAPPENED
                if LM_name in modules.keys():
                    del modules[LM_name]
                # Exec FAIL -> recovery action in SocketServer
                return False
        # Exec OK
        return True
    msgobj("SHELL: type help for single word commands (built-in)")
    msgobj("SHELL: for LM exec: [1](LM)module [2]function [3...]optional params")
    # Exec OK
    return True


def execLMCore(argument_list, msgobj=None):
    # @1 Run Thread if requested and enable
    # Cache message obj in cwr
    cwr = console_write if msgobj is None else msgobj
    state = startBgJob(argument_list=argument_list, msg=cwr)
    if state:
        return True
    # @2 Run simple task
    # |- Thread locking NOT available
    if BgTask is None:
        return __exec_lm_core(argument_list, msgobj=cwr)
    # |- Thread locking available
    with BgTask():
        state = __exec_lm_core(argument_list, msgobj=cwr)
    return state
