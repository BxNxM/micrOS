from os import listdir
try:
    from ConfigHandler import cfg
except Exception as e:
    print("Failed to import ConfigHandler: {}".format(e))
try:
    from gc import collect, mem_free
except:
    pass

#########################################################
#                    MODULE VARIABLES                   #
#########################################################
CONFIGURE_MODE = False

#########################################################
#             SHELL Interpreter FUNCTIONS               #
#########################################################
def shell(msg=None, WebServerObj=None):
    try:
        __shell(msg, WebServerObj)
    except Exception as e:
        WebServerObj.reply_message("Runtime error: {}".format(e))

def __shell(msg, WebServerObj):
    global CONFIGURE_MODE
    if msg is None or msg == "":
        return ""
    msg_list = msg.strip().split()

    # CONFIGURE MODE
    if msg_list[0] == "configure" or msg_list[0] == "conf":
        if len(msg_list) == 1:
            CONFIGURE_MODE = True
            WebServerObj.pre_prompt = "[configure] "
        msg_list = []
    elif msg_list[0] == "noconfigure" or msg_list[0] == "noconf":
        if len(msg_list) == 1:
            CONFIGURE_MODE = False
            WebServerObj.pre_prompt = ""
        msg_list = []

    # HELP MSG
    if "help" in msg_list:
        WebServerObj.reply_message("hello - default hello msg - identify device (WebServer)")
        WebServerObj.reply_message("exit  - exit from shell socket prompt (WebServer)")
        WebServerObj.reply_message("Configure mode:")
        WebServerObj.reply_message("   configure|conf     - Enter conf mode")
        WebServerObj.reply_message("         Key          - Get value")
        WebServerObj.reply_message("         Key:Value    - Set value")
        WebServerObj.reply_message("         dump         - Dump all data")
        WebServerObj.reply_message("   noconfigure|noconf - Exit conf mod")
        WebServerObj.reply_message("Command mode:")
        show_LMs_functions(WebServerObj)
        msg_list = []

    # EXECUTE:
    # @1 Configure mode
    if CONFIGURE_MODE and len(msg_list) != 0:
        configure(msg_list, WebServerObj)
    # @2 Command mode
    elif not CONFIGURE_MODE and len(msg_list) != 0:
        command(msg_list, WebServerObj)


#########################################################
#               CONFIGURE MODE HANDLER                  #
#########################################################
def configure(attributes, WebServerObj):
    # Get value
    if len(attributes) == 1:
        if attributes[0] == "dump":
            WebServerObj.reply_message(cfg.get_all())
        else:
            key = attributes[0]
            WebServerObj.reply_message(cfg.get(key))
    # Set value
    elif len(attributes) == 2:
        key = attributes[0]
        value = attributes[1]
        WebServerObj.reply_message(cfg.put(key, value))
    else:
        WebServerObj.reply_message("Too many arguments - [1] key [2] value")

#########################################################
#               COMMAND MODE & LMS HANDLER              #
#########################################################
def command(attributes_list, WebServerObj):
    execute_LM_function(attributes_list, WebServerObj)

def load_LMs():
    LM_MODULE_LIST = [i for i in listdir() if i.startswith('LM_')]
    LM_MODULE_LIST = [i.replace('.py', '') for i in LM_MODULE_LIST if i.endswith('.py')]
    return LM_MODULE_LIST

def show_LMs_functions(WebServerObj):
    for LM in load_LMs():
        exec("import " + str(LM))
        LM_functions = eval("dir({})".format(LM))
        LM_functions = [i for i in LM_functions if not i.startswith('__')]
        WebServerObj.reply_message("   {}".format(LM))
        for func in LM_functions:
            WebServerObj.reply_message("   {}{}".format(" "*len(LM), func))

def execute_LM_function(argument_list, WebServerObj):
    '''
    1. param. - LM name, i.e. LM_commands
    2. param. - function call with parameters, i.e. a()
    '''
    if len(argument_list) >= 2:
        LM_name = argument_list[0]
        LM_function_call = "".join(argument_list[1:])
        LM_function = argument_list[1].split('(')[0]
    try:
        WebServerObj.server_console("from {} import {}".format(LM_name, LM_function))
        exec("from {} import {}".format(LM_name, LM_function))
        WebServerObj.reply_message(str(eval("{}".format(LM_function_call))))
    except Exception as e:
        WebServerObj.reply_message("execute_LM_function: " + str(e))
        if "memory allocation failed" in str(e):
            collect()
            WebServerObj.reply_message("execute_LM_function -gc-ollect-memfree: " + str(mem_free()))

def reset_shell_state():
    global CONFIGURE_MODE
    CONFIGURE_MODE = False

