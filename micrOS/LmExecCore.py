from sys import modules


def exec_lm_core(arg_list, msgobj):
    """
    [1] module name (LM)
    [2] function
    [3...] parameters (separator: space)
    NOTE: msgobj - must be a function with one input param (stdout/file/stream)
    """
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
            if not json_mode and isinstance(lm_output, dict):
                # Format dict output - human readable
                lm_output = '\n'.join(["{}: {}".format(key, value) for key, value in lm_output.items()])
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
