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

#################################################################
#               Interpreter shell CORE executor                 #
#################################################################


def execLMPipe(taskstr):
    """
    Input: taskstr contains LM calls separated by ;
    """
    st = True
    try:
        for cmd in (cmd.strip().split() for cmd in taskstr.split(';')):
            buf = execLMCore(cmd)
            st &= buf
            if not buf: console_write("|-[LM-PIPE] task error: {}".format(cmd))
    except Exception as e:
        console_write("[LM-PIPE] pipe error: {}\n{}".format(taskstr, e))
        st &= False
    return st


def execLMCore(argument_list, msgobj=None):
    """
    [1] module name (LM)
    [2] function
    [3...] parameters (separator: space)
    NOTE: msgobj is None from Interrupts and Hooks - shared functionality
    """
    # Cache message obj
    cwr = console_write if msgobj is None else msgobj
    # Check json mode for LM execution
    json_mode = True if argument_list[-1] == '>json' else False
    if json_mode:
        del argument_list[-1]
    # LoadModule execution
    if len(argument_list) >= 2:
        LM_name, LM_function, LM_function_params = "LM_{}".format(argument_list[0]), argument_list[1], ', '.join(argument_list[2:])
        try:
            # --- LM LOAD & EXECUTE --- #
            # [1] LOAD MODULE
            if LM_name not in modules.keys():
                exec("import {}".format(LM_name))
            # [2] EXECUTE FUNCTION FROM MODULE - over msgobj or /dev/null
            lm_output = eval("{}.{}({})".format(LM_name, LM_function, LM_function_params))
            if msgobj is not None:
                if not json_mode and isinstance(lm_output, dict):
                    # human readable format (not json mode) but dict
                    lm_output = '\n'.join(["{}: {}".format(key, value) for key, value in lm_output.items()])
                    msgobj(str(lm_output))
                else:
                    # native return value (not dict) OR json mode raw dict output
                    msgobj(str(lm_output))
            # ------------------------- #
        except Exception as e:
            cwr("execute_LM_function {}->{}: {}".format(LM_name, LM_function, e))
            if 'memory allocation failed' in str(e) or 'is not defined' in str(e):
                # UNLOAD MODULE IF MEMORY ERROR HAPPENED
                if LM_name in modules.keys():
                    del modules[LM_name]
                # Exec FAIL -> recovery action in SocketServer
                return False
        # Exec OK
        return True
    cwr("SHELL: type help for single word commands (built-in)")
    cwr("SHELL: for LM exec: [1](LM)module [2]function [3...]optional params")
    # Exec OK
    return True
