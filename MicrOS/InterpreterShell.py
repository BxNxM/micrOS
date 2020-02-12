try:
    from ConfigHandler import cfgget, cfgput, cfgget_all
except Exception as e:
    print("Failed to import ConfigHandler: {}".format(e))

#########################################################
#                    MODULE VARIABLES                   #
#########################################################
CONFIGURE_MODE = False

#########################################################
#             SHELL Interpreter FUNCTIONS               #
#########################################################
def shell(msg=None, SocketServerObj=None):
    try:
        __shell(msg, SocketServerObj)
    except Exception as e:
        SocketServerObj.reply_message("Runtime error: {}".format(e))

def __shell(msg, SocketServerObj):
    global CONFIGURE_MODE
    if msg is None or msg == "":
        return ""
    msg_list = msg.strip().split()

    # CONFIGURE MODE
    if msg_list[0] == "configure" or msg_list[0] == "conf":
        if len(msg_list) == 1:
            CONFIGURE_MODE = True
            SocketServerObj.pre_prompt = "[configure] "
        msg_list = []
    elif msg_list[0] == "noconfigure" or msg_list[0] == "noconf":
        if len(msg_list) == 1:
            CONFIGURE_MODE = False
            SocketServerObj.pre_prompt = ""
        msg_list = []

    # HELP MSG
    if "help" in msg_list:
        SocketServerObj.reply_message("hello - default hello msg - identify device (SocketServer)")
        SocketServerObj.reply_message("exit  - exit from shell socket prompt (SocketServer)")
        SocketServerObj.reply_message("Configure mode:")
        SocketServerObj.reply_message("   configure|conf     - Enter conf mode")
        SocketServerObj.reply_message("         Key          - Get value")
        SocketServerObj.reply_message("         Key:Value    - Set value")
        SocketServerObj.reply_message("         dump         - Dump all data")
        SocketServerObj.reply_message("   noconfigure|noconf - Exit conf mod")
        SocketServerObj.reply_message("Command mode:")
        show_LMs_functions(SocketServerObj)
        msg_list = []

    # EXECUTE:
    # @1 Configure mode
    if CONFIGURE_MODE and len(msg_list) != 0:
        configure(msg_list, SocketServerObj)
    # @2 Command mode
    elif not CONFIGURE_MODE and len(msg_list) != 0:
        command(msg_list, SocketServerObj)


#########################################################
#               CONFIGURE MODE HANDLER                  #
#########################################################
def configure(attributes, SocketServerObj):
    # Get value
    if len(attributes) == 1:
        if attributes[0] == "dump":
            SocketServerObj.reply_message(cfgget_all())
        else:
            key = attributes[0]
            SocketServerObj.reply_message(cfgget(key))
    # Set value
    elif len(attributes) == 2:
        key = attributes[0]
        value = attributes[1]
        SocketServerObj.reply_message(cfgput(key, value))
    else:
        SocketServerObj.reply_message("Too many arguments - [1] key [2] value")

#########################################################
#               COMMAND MODE & LMS HANDLER              #
#########################################################
def command(attributes_list, SocketServerObj):
    execute_LM_function(attributes_list, SocketServerObj)

def load_LMs():
    from os import listdir
    LM_MODULE_LIST = [i for i in listdir() if i.startswith('LM_')]
    LM_MODULE_LIST = [i.replace('.py', '') for i in LM_MODULE_LIST if i.endswith('.py')]
    del listdir
    return LM_MODULE_LIST

def show_LMs_functions(SocketServerObj):
    for LM in load_LMs():
        exec("import " + str(LM))
        LM_functions = eval("dir({})".format(LM))
        LM_functions = [i for i in LM_functions if not i.startswith('__')]
        LM = LM.replace('LM_', '')
        SocketServerObj.reply_message("   {}".format(LM))
        for func in LM_functions:
            SocketServerObj.reply_message("   {}{}".format(" "*len(LM), func))

def execute_LM_function(argument_list, SocketServerObj):
    '''
    1. param. - LM name, i.e. LM_commands
    2. param. - function call with parameters, i.e. a()
    '''
    from machine import disable_irq, enable_irq
    if len(argument_list) >= 2:
        LM_name = "LM_{}".format(argument_list[0])
        LM_function_call = "".join(argument_list[1:])
        LM_function = argument_list[1].split('(')[0]
        if "(" not in LM_function_call and ")" not in LM_function_call:
            LM_function_call = "{}()".format(LM_function)
    try:
        SocketServerObj.server_console("from {} import {}".format(LM_name, LM_function))
        state = disable_irq()
        exec("from {} import {}".format(LM_name, LM_function))
        enable_irq(state)
        SocketServerObj.reply_message(str(eval("{}".format(LM_function_call))))
    except Exception as e:
        SocketServerObj.reply_message("execute_LM_function: " + str(e))
        if "memory allocation failed" in str(e):
            from gc import collect, mem_free
            collect()
            SocketServerObj.reply_message("execute_LM_function -gc-ollect-memfree: " + str(mem_free()))
            del collect, mem_free

def reset_shell_state():
    global CONFIGURE_MODE
    CONFIGURE_MODE = False

