# VERSION: 1.0

# SET IT LATER FROM CONFIG
PLED_STAT = False
DEBUG_PRINT = True
pLED = None

#################################################################
#                     CONSOLE WRITE FUNCTIONS                   #
#################################################################
def progress_led_toggle_adaptor(func):
    def wrapper(*args, **kwargs):
        global pLED, PLED_STAT
        if pLED and PLED_STAT: pLED.toggle()
        output = func(*args, **kwargs)
        if pLED and PLED_STAT: pLED.toggle()
        return output
    return wrapper

@progress_led_toggle_adaptor
def console_write(msg):
    global DEBUG_PRINT
    if DEBUG_PRINT:
        print(msg)

#################################################################
#                           IMPORTS                             #
#################################################################
try:
    from ujson import load, dump
except Exception as e:
    console_write("ujson module not found: " + str(e))
    from json import load, dump

try:
    import ProgressLED as pLED
except Exception as e:
    pLED = False

#################################################################
#                       MODULE CONFIG
#################################################################
CONFIG_PATH="node_config.json"
DEFAULT_CONFIGURATION_TEMPLATE = {"staessid": "your_wifi_name",
                                  "stapwd": "your_wifi_passwd",
                                  "devfid": "slim01",
                                  "appwd": "Admin123",
                                  "pled": True,
                                  "dbg": False,
                                  "nwmd": "n/a",
                                  "hwuid": "n/a",
                                  "soctout": 100,
                                  "socport": 9008,
                                  "devip": "n/a",
                                  "timirq": True,
                                  "extirq": True,
                                  "gmttime": +1}

#################################################################
#                  CONFIGHANDLER  FUNCTIONS                     #
#################################################################
def cfgget(key):
    try:
        return __read_cfg_file().get(key, None)
    except Exception as e:
        console_write("[CONFIGHANDLER] Get config value error: {}".format(e))
    return None

def cfgput(key, value):
    try:
        value = __value_type_handler(key, value)
        if value is not None:
            cfg_dict_buffer = __read_cfg_file()
            cfg_dict_buffer[key] = value
            __write_cfg_file(cfg_dict_buffer)
            del cfg_dict_buffer
            return True
    except:
        pass
    return False

def cfgprint_all():
    data_struct = dict(__read_cfg_file())
    if isinstance(data_struct, dict):
        for key, value in data_struct.items():
            console_write("  {}: {}".format(key, value))
    else:
        console_write("[CONFIGHANDLER] data_struct not dict: " + str(data_struct))

def cfgget_all():
    return __read_cfg_file()

def __read_cfg_file():
    global CONFIG_PATH
    try:
        with open(CONFIG_PATH, 'r') as f:
            data_dict = load(f)
    except Exception as e:
        console_write("[CONFIGHANDLER] __read_cfg_file error {} (json): {}".format(CONFIG_PATH, e))
        data_dict = {}
    return data_dict

def __write_cfg_file(dictionary):
    global CONFIG_PATH
    if not isinstance(dictionary, dict):
        console_write("[CONFIGHANDLER] __write_cfg_file - config data struct should be a dict!")
        return False
    try:
        with open(CONFIG_PATH, 'w') as f:
            dump(dictionary, f)
        return True
    except Exception as e:
            console_write("[CONFIGHANDLER] __write_cfg_file error {} (json): {}".format(CONFIG_PATH, e))
            return False

def __inject_default_conf():
    global DEFAULT_CONFIGURATION_TEMPLATE
    if not isinstance(DEFAULT_CONFIGURATION_TEMPLATE, dict):
        console_write("__inject_default_conf input data type must be dict")
        return
    DEFAULT_CONFIGURATION_TEMPLATE.update(__read_cfg_file())
    try:
        if __write_cfg_file(DEFAULT_CONFIGURATION_TEMPLATE):
            console_write("[CONFIGHANDLER] Inject default data struct successful")
        else:
            console_write("[CONFIGHANDLER] Inject default data struct failed")
    except Exception as e:
        console_write(e)

def __value_type_handler(key, value):
    value_in_cfg = cfgget(key)
    try:
        if isinstance(value_in_cfg, bool):
            if value in ['True', 'true']:
                value = True
            elif value in ['False', 'false']:
                value = False
            elif isinstance(value, bool):
                value = value
            else:
                raise Exception()
            return value
        elif isinstance(value_in_cfg, str):
            return str(value)
        elif isinstance(value_in_cfg, int):
            return int(value)
        elif isinstance(value_in_cfg, float):
            return float(value)
    except Exception as e:
        console_write("Input value type error! {}".format(e))
        return None

#################################################################
#                       MODULE AUTO INIT                        #
#################################################################
def __init_module():
    global PLED_STAT, DEBUG_PRINT
    __inject_default_conf()
    try:
        PLED_STAT = cfgget("pled")
        DEBUG_PRINT = cfgget("dbg")
    except Exception as e:
        print(e)
        DEBUG_PRINT = False

if "ConfigHandler" in __name__:
    __init_module()

#################################################################
#                            DEMO                               #
#################################################################
def confighandler_demo():
    __init_module()
    cfgprint_all()
    console_write("Write console msg ...")

if __name__ == "__main__":
    confighandler_demo()
