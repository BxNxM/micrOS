#################################################################
#                           IMPORTS                             #
#################################################################
from sys import modules

#################################################################
#               Interpreter shell CORE executor                 #
#################################################################
# USED IN: InterpreterShell, InterruptHandler, Hooks


def execute_LM_function_Core(argument_list, SocketServerObj=None):
    '''
    1. param. - LM name, i.e. LM_commands
    2. param. - function call with parameters, i.e. a()
    NOTE: SocketServerObj is None from Interrupts and Hooks - shared functionality
    '''
    recovery_query = False
    if len(argument_list) >= 2:
        LM_name = "LM_{}".format(argument_list[0])
        LM_function = argument_list[1].split('(')[0]
        LM_function_call = "".join(argument_list[1:])
        if not LM_function_call.endswith(')'):
            # Auto complete brackets "(" ")" with arguments
            # ARG 0: LM_function
            # ARG 1: LM function arguments (without '(' and/or ')')
            LM_function_call = "{}({})".format(LM_function, str(" ".join(" ".join(argument_list[1:]).split('(')[1:])).replace(')', ''))
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
                # UNLOAD MODULE IF MEMORY ERROR HAPPENED
                if LM_name in modules.keys():
                    del modules[LM_name]
                recovery_query = True
    else:
        if SocketServerObj is not None:
            SocketServerObj.reply_message("SHELL: type help for base (single word) commands")
            SocketServerObj.reply_message("SHELL: for LM exec: [1](LM_)module [2]function[3](optional params.)")
        else:
            print("SHELL: Missing argument: [1](LM_)module [2]function[3](optional params.)")
    # RETURN WITH HEALTH STATE - TRUE :) -> NO ACTION -or- FALSE :( -> RECOVERY ACTION
    return not recovery_query

