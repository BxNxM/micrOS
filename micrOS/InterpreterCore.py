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
from Debug import console_write
from json import dumps
from micropython import schedule


#################################################################
#               Interpreter shell CORE executor                 #
#################################################################


def exec_lm_pipe(taskstr):
    """
    Input: taskstr contains LM calls separated by ;
    Used for execute config callback parameters (IRQs and BootHook)
    """
    try:
        # Handle config default empty value (do nothing)
        if taskstr.startswith('n/a'):
            return True
        # Execute individual commands - msgobj->"/dev/null"
        for cmd in (cmd.strip().split() for cmd in taskstr.split(';')):
            try:
                schedule(exec_lm_core, cmd)
            except Exception as e:
                console_write("|-[LM-PIPE] task error: {}: {}".format(cmd, e))
    except Exception as e:
        console_write("[IRQ-PIPE] error: {}\n{}".format(taskstr, e))
        return False
    return True


def exec_lm_pipe_schedule(taskstr):
    """
    Wrapper for exec_lm_pipe
    - fix IRQ execution limit - magic
    """
    try:
        schedule(exec_lm_pipe, taskstr)
        return True
    except:
        return False


def exec_lm_core(arg_list, msgobj=None):
    """
    MAIN FUNCTION TO RUN STRING MODULE.FUNCTION EXECUTIONS
    [1] module name (LM)
    [2] function
    [3...] parameters (separator: space)
    NOTE: msgobj - must be a function with one input param (stdout/file/stream)
    """
    # Handle default msgobj >dev/null
    if msgobj is None:
        msgobj = lambda msg: None

    # Dict output user format / jsonify
    def __format_out(json_mode, lm_func, output):
        if isinstance(output, dict):
            if json_mode:
                return dumps(output)
            # Format dict output - human readable
            return '\n'.join([" {}: {}".format(key, value) for key, value in lm_output.items()])
        # Handle output data stream
        if lm_func == 'help':
            if json_mode:
                return dumps(output)
            # Format help msg - human readable
            return '\n'.join([' {},'.format(out) for out in output])
        return output

    # Check json mode for LM execution
    json_mode = arg_list[-1] == '>json'
    if json_mode:
        del arg_list[-1]
    # LoadModule execution
    if len(arg_list) >= 2:
        lm_mod, lm_func, lm_params = "LM_{}".format(arg_list[0]), arg_list[1], ', '.join(arg_list[2:])
        try:
            # --- LM LOAD & EXECUTE --- #
            # [1] LOAD MODULE
            exec("import {}".format(lm_mod))
            # [2] EXECUTE FUNCTION FROM MODULE - over msgobj (socket or stdout)
            lm_output = eval("{}.{}({})".format(lm_mod, lm_func, lm_params))
            # Handle output data stream
            lm_output = __format_out(json_mode, lm_func, lm_output)
            # Return LM exec result via msgobj
            msgobj(str(lm_output))
            return True
            # ------------------------- #
        except Exception as e:
            msgobj("exec_lm_core {}->{}: {}".format(lm_mod, lm_func, e))
            if 'memory allocation failed' in str(e) or 'is not defined' in str(e):
                # UNLOAD MODULE IF MEMORY ERROR HAPPENED
                if lm_mod in modules.keys():
                    del modules[lm_mod]
                # Exec FAIL -> recovery action in SocketServer
                return False
    msgobj("SHELL: type help for single word commands (built-in)")
    msgobj("SHELL: for LM exec: [1](LM)module [2]function [3...]optional params")
    # Exec OK
    return True
