# VERSION: 1.0
from time import sleep

# SET IT LATER FROM CONFIG
PLED_STAT = False
DEBUG_PRINT = True
pLED = None
CONF_LOCK = False

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
def default_config():
    DEFAULT_CONFIGURATION_TEMPLATE = {"version": "n/a",
                                      "staessid": "your_wifi_name",
                                      "stapwd": "your_wifi_passwd",
                                      "devfid": "slim01",
                                      "appwd": "ADmin123",
                                      "pled": True,
                                      "dbg": True,
                                      "nwmd": "n/a",
                                      "hwuid": "n/a",
                                      "soctout": 100,
                                      "socport": 9008,
                                      "devip": "n/a",
                                      "timirq": False,
                                      "timirqcbf": "n/a",
                                      "timirqseq": 3000,
                                      "extirq": False,
                                      "extirqcbf": "n/a",
                                      "gmttime": +1}
    return DEFAULT_CONFIGURATION_TEMPLATE

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
            del cfg_dict_buffer, value
            return True
    except:
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

def __read_cfg_file(nosafe=False):
    global CONF_LOCK
    data_dict = {}
    while len(data_dict) <= 0:
        try:
            if not CONF_LOCK:
                CONF_LOCK = True
                with open(CONFIG_PATH, 'r') as f:
                    data_dict = load(f)
                CONF_LOCK = False
            else:
                console_write("[CONFIGHANDLER] __read_cfg_file: LOCK")
                sleep(0.2)
        except Exception as e:
            CONF_LOCK = False
            console_write("[CONFIGHANDLER] __read_cfg_file error {} (json): {}".format(CONFIG_PATH, e))
            if nosafe:
                break
            sleep(0.2)
    return data_dict

def __write_cfg_file(dictionary):
    global CONF_LOCK
    if not isinstance(dictionary, dict):
        console_write("[CONFIGHANDLER] __write_cfg_file - config data struct should be a dict!")
        return False

    state = False
    while not state:
        try:
            if not CONF_LOCK:
                with open(CONFIG_PATH, 'w') as f:
                    dump(dictionary, f)
                state = True
            else:
                console_write("[CONFIGHANDLER] __write_cfg_file: LOCK")
                sleep(0.2)
        except Exception as e:
            console_write("[CONFIGHANDLER] __write_cfg_file error {} (json): {}".format(CONFIG_PATH, e))
            state = False
        sleep(0.2)
    return state

def __inject_default_conf():
    default_config_dict = default_config()
    if not isinstance(default_config_dict, dict):
        console_write("__inject_default_conf input data type must be dict")
        return
    default_config_dict.update(__read_cfg_file(nosafe=True))
    try:
        if __write_cfg_file(default_config_dict):
            console_write("[CONFIGHANDLER] Inject default data struct successful")
        else:
            console_write("[CONFIGHANDLER] Inject default data struct failed")
    except Exception as e:
        console_write(e)
    finally:
        del default_config_dict

def __value_type_handler(key, value):
    value_in_cfg = cfgget(key)
    try:
        if isinstance(value_in_cfg, bool):
            del value_in_cfg
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
            del value_in_cfg
            return str(value)
        elif isinstance(value_in_cfg, int):
            del value_in_cfg
            return int(value)
        elif isinstance(value_in_cfg, float):
            del value_in_cfg
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
        console_write("[CONFIGHANDLER] module init error: {}".format(e))
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
