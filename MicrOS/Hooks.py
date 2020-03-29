from ConfigHandler import cfgget, console_write
from InterpreterShell import execute_LM_function_Core
try:
    from micropython import mem_info
except:
    mem_info = None
try:
    from ConfigHandler import cfgget
except Exception as e:
    print("Failed to import ConfigHandler: {}".format(e))


def bootup_hook():
    '''
    Executes when system boots up.
    '''
    console_write("[BOOT HOOKS] EXECUTION...")
    if cfgget('boothook') is not None and cfgget('boothook').lower() != 'n/a':
        for shell_cmd in [ cmd.strip() for cmd in tuple(cfgget('boothook').split(';')) if len(cmd.split()) > 1 ]:
            console_write("|-[BOOT HOOKS] SHELL EXEC: {}".format(shell_cmd))
            try:
                state = execute_LM_function_Core(shell_cmd.split())
                console_write("|-[BOOT HOOKS] state: {}".format(state))
            except Exception as e:
                console_write("|--[BOOT HOOKS] error: {}".format(e))


def profiling_info(label=""):
    if cfgget('dbg'):
        console_write("{} [PROFILING INFO] - {} {}".format('~'*5, label, '~'*5))
        try:
            mem_info()
        except Exception as e:
            console_write("MEM INFO QUERY ERROR: {}".format(e))
        console_write("~"*30)
    else:
        console_write("[PROFILING INFO] SKIP dbg:{}".format(cfgget('dbg')))
