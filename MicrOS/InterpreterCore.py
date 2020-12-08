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

#################################################################
#               Interpreter shell CORE executor                 #
#################################################################


def execute_LM_function_Core(argument_list, SocketServerObj=None):
    """
    [1] module name (LM)
    [2] function
    [3...] parameters (separator: space)
    NOTE: SocketServerObj is None from Interrupts and Hooks - shared functionality
    """
    json_mode = False
    # Check json mode for LM execution
    if argument_list[-1] == '>json':
        del argument_list[-1]
        json_mode = True

    # health - True [no action] - False [system soft recovery]
    health = True
    if len(argument_list) >= 2:
        LM_name, LM_function, LM_function_params = "LM_{}".format(argument_list[0]), argument_list[1], ', '.join(argument_list[2:])
        try:
            # --- LM LOAD & EXECUTE --- #
            # [1] LOAD MODULE
            if LM_name not in modules.keys():
                exec("import {}".format(LM_name))
            # [2] EXECUTE FUNCTION FROM MODULE - over SocketServerObj or /dev/null
            lm_output = eval("{}.{}({})".format(LM_name, LM_function, LM_function_params))
            if SocketServerObj is not None:
                if not json_mode and isinstance(lm_output, dict):
                    # human readable format (not json mode) but dict
                    lm_output = '\n'.join(["{}: {}".format(key, value) for key, value in lm_output.items()])
                    SocketServerObj.reply_message(str(lm_output))
                else:
                    # native return value (not dict) OR json mode raw dict output
                    SocketServerObj.reply_message(str(lm_output))
            # ------------------------- #
        except Exception as e:
            # ERROR MSG: - over SocketServerObj or stdout
            print("execute_LM_function {}->{}: {}".format(LM_name, LM_function, e))
            if SocketServerObj is not None:
                SocketServerObj.reply_message("execute_LM_function {}->{}: {}".format(LM_name, LM_function, e))
            if "memory allocation failed" in str(e):
                # UNLOAD MODULE IF MEMORY ERROR HAPPENED
                if LM_name in modules.keys():
                    del modules[LM_name]
                health = False
        # RETURN WITH HEALTH STATE - TRUE :) -> NO ACTION -or- FALSE :( -> RECOVERY ACTION
        return health

    # Syntax error show help msg
    print("SHELL: Missing argument: [1](LM)module [2]function [3...]optional params")
    if SocketServerObj is not None:
        SocketServerObj.reply_message("SHELL: type help for single word commands (built-in)")
        SocketServerObj.reply_message("SHELL: for LM exec: [1](LM)module [2]function [3...]optional params")
    # RETURN WITH HEALTH STATE - TRUE :) -> NO ACTION -or- FALSE :( -> RECOVERY ACTION
    return health
