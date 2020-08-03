"""
Module is responsible for configuration management
dedicated to micrOS framework.
- get / set
- cache handling
- read / write to file
- secure type handling
- default parameter injection (update)

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                           IMPORTS                             #
#################################################################
from time import sleep
from json import load, dump

try:
    from machine import Pin
    from LogicalPins import get_pin_on_platform_by_key
    PLED = Pin(get_pin_on_platform_by_key('builtin'), Pin.OUT)
except Exception as e:
    print("[WARNING] Progressled not available on device: {}".format(e))
    PLED = None

# SET IT LATER FROM CONFIG
__DEBUG_PRINT = True
__CONFIG_CACHE = {}
# - MicrOS config
__CONFIG_PATH = "node_config.json"

#################################################################
#                       MODULE CONFIG
#################################################################


def default_config():
    default_configuration_template = {"version": "n/a",
                                      "staessid": "your_wifi_name",
                                      "stapwd": "your_wifi_passwd",
                                      "devfid": "node01",
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
                                      "irqmembuf": 1300,
                                      "extirq": False,
                                      "extirqcbf": "n/a",
                                      "boothook": "n/a",
                                      "gmttime": +1,
                                      "boostmd": True}
    return default_configuration_template

#################################################################
#                     CONSOLE WRITE FUNCTIONS                   #
#################################################################


def progress_led_toggle_adaptor(func):
    def wrapper(*args, **kwargs):
        if PLED is not None: PLED.value(not PLED.value())
        output = func(*args, **kwargs)
        if PLED is not None: PLED.value(not PLED.value())
        return output
    return wrapper


@progress_led_toggle_adaptor
def console_write(msg):
    if __DEBUG_PRINT:
        print(msg)


#################################################################
#                  CONFIGHANDLER  FUNCTIONS                     #
#################################################################


def cfgget(key):
    try:
        return __read_cfg_file().get(key, None)
    except Exception as e:
        console_write("[CONFIGHANDLER] Get config value error: {}".format(e))
    return None


def cfgput(key, value, type_check=False):
    if cfgget(key) == value:
        return True
    try:
        if type_check:
            value = __value_type_handler(key, value)
        if value is not None:
            cfg_dict_buffer = __read_cfg_file()
            cfg_dict_buffer[key] = value
            __write_cfg_file(cfg_dict_buffer)
            del cfg_dict_buffer, value
            return True
    except Exception:
        pass
    return False


def cfgget_all():
    return __read_cfg_file()


#################################################################
#             CONFIGHANDLER  INTERNAL FUNCTIONS                 #
#################################################################


def __read_cfg_file(nosafe=False):
    global __CONFIG_CACHE
    while True:
        try:
            if len(__CONFIG_CACHE) == 0:
                # READ JSON CONFIG
                with open(__CONFIG_PATH, 'r') as f:
                    __CONFIG_CACHE = load(f)
            break
        except Exception as e:
            console_write("[CONFIGHANDLER] __read_cfg_file error {} (json): {}".format(__CONFIG_PATH, e))
            # Write out initial config, if no config exists.
            if nosafe:
                break
            sleep(0.2)
    return __CONFIG_CACHE


def __write_cfg_file(dictionary):
    global __CONFIG_CACHE
    # WRITE CACHE
    __CONFIG_CACHE = dictionary
    while True:
        try:
            # WRITE JSON CONFIG
            with open(__CONFIG_PATH, 'w') as f:
                dump(dictionary, f)
            break
        except Exception as e:
            console_write("[CONFIGHANDLER] __write_cfg_file error {} (json): {}"
                          .format(__CONFIG_PATH, e))
        sleep(0.2)
    return True


def __inject_default_conf():
    default_config_dict = default_config()
    live_config = __read_cfg_file(nosafe=True)
    default_config_dict.update(live_config)
    if default_config_dict['dbg']:
        console_write("[CONFIGHANDLER] inject config:\n{}".format(default_config_dict))
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
            if str(value).lower() == 'true':
                return True
            if str(value).lower() == 'false':
                return False
            raise Exception("__value_type_handler type handling error")
        if isinstance(value_in_cfg, str):
            del value_in_cfg
            return str(value)
        if isinstance(value_in_cfg, int):
            del value_in_cfg
            return int(value)
        if isinstance(value_in_cfg, float):
            del value_in_cfg
            return float(value)
    except Exception:
        console_write("Input value type error! {}".format(e))
    return None

#################################################################
#                       MODULE AUTO INIT                        #
#################################################################


if "ConfigHandler" in __name__:
    __inject_default_conf()                     # Validate / update / create user config
    __DEBUG_PRINT = cfgget('dbg')                 # Inject from user conf
    if not cfgget('pled'): PLED = None          # Turn off progressled if necesary
