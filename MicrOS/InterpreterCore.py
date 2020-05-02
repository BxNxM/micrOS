#################################################################
#                           IMPORTS                             #
#################################################################
from sys import modules

#################################################################
#               Interpreter shell CORE executor                 #
#################################################################
# USED IN: InterpreterShell, InterruptHandler, Hooks


def execute_LM_function_Core(argument_list, SocketServerObj=None):
    """
    1. param. - LM name, i.e. LM_commands
    2. param. - function call with parameters, i.e. a()
    NOTE: SocketServerObj is None from Interrupts and Hooks - shared functionality
    """
    # health - True [no action] - False [system soft recovery]
    health = True
    if len(argument_list) >= 2:
        LM_name, LM_function, LM_function_call = "LM_{}".format(argument_list[0]), argument_list[1].split('(')[0], "".join(argument_list[1:])
        if not LM_function_call.endswith(')'):
            # Auto complete brackets "(" ")" with arguments
            # ARG 0: LM_function
            # ARG 1: LM function arguments (without '(' and/or ')')
            LM_function_call = "{}({})".format(LM_function, str(" ".join(" ".join(argument_list[1:]).split('(')[1:])).replace(')', ''))
        try:
            # --- LM LOAD & EXECUTE --- #
            if SocketServerObj is not None: SocketServerObj.server_console("from {} import {}".format(LM_name, LM_function))
            # [1] LOAD MODULE
            exec("from {} import {}".format(LM_name, LM_function))
            # [2] EXECUTE FUNCTION FROM MODULE - over SocketServerObj or /dev/null
            eval("{}".format(LM_function_call)) if SocketServerObj is None else SocketServerObj.reply_message(str(eval("{}".format(LM_function_call))))
            # ------------------------- #
        except Exception as e:
            # ERROR MSG: - over SocketServerObj or stdout
            print("execute_LM_function {}->{}: {}".format(LM_name, LM_function, e)) if SocketServerObj is None else SocketServerObj.reply_message("execute_LM_function {}->{}: {}".format(LM_name, LM_function, e))
            if "memory allocation failed" in str(e):
                # UNLOAD MODULE IF MEMORY ERROR HAPPENED
                if LM_name in modules.keys():
                    del modules[LM_name]
                health = False
    else:
        if SocketServerObj is not None:
            SocketServerObj.reply_message("SHELL: type help for base (single word) commands")
            SocketServerObj.reply_message("SHELL: for LM exec: [1](LM_)module [2]function[3](optional params.)")
        else:
            print("SHELL: Missing argument: [1](LM_)module [2]function[3](optional params.)")
    # RETURN WITH HEALTH STATE - TRUE :) -> NO ACTION -or- FALSE :( -> RECOVERY ACTION
    return health
