#################################################################
#                           IMPORTS                             #
#################################################################
from time import sleep
from json import load, dump

try:
    from machine import Pin
    from LogicalPins import getPlatformValByKey
    PLED = Pin(getPlatformValByKey('progressled'), Pin.OUT)
except Exception as e:
    print("[WARNING] Progressled not available on device: {}".format(e))
    PLED = None

# SET IT LATER FROM CONFIG
DEBUG_PRINT = True
CONFIG_CACHE = {}
# - MicrOS config
CONFIG_PATH = "node_config.json"

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
                                      "irqmembuf": 1000,
                                      "extirq": False,
                                      "extirqcbf": "n/a",
                                      "boothook": "n/a",
                                      "gmttime": +1}
    return default_configuration_template

#################################################################
#                     CONSOLE WRITE FUNCTIONS                   #
#################################################################


def progress_led_toggle_adaptor(func):
    def wrapper(*args, **kwargs):
        try:
            if PLED is not None: PLED.value(not PLED.value())
        except: pass
        output = func(*args, **kwargs)
        try:
            if PLED is not None: PLED.value(not PLED.value())
        except: pass
        return output
    return wrapper


@progress_led_toggle_adaptor
def console_write(msg):
    if DEBUG_PRINT:
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
    except:
        return False


def cfgget_all():
    return __read_cfg_file()


#################################################################
#             CONFIGHANDLER  INTERNAL FUNCTIONS                 #
#################################################################


def __read_cfg_file(nosafe=False):
    global CONFIG_CACHE
    data_dict = {}
    while len(data_dict) <= 0:
        try:
            if len(CONFIG_CACHE) == 0:
                # READ JSON CONFIG
                with open(CONFIG_PATH, 'r') as f:
                    data_dict = load(f)
                    CONFIG_CACHE = data_dict
            else:
                # READ CACHE
                data_dict = CONFIG_CACHE
        except Exception as e:
            console_write("[CONFIGHANDLER] __read_cfg_file error {} (json): {}".format(CONFIG_PATH, e))
            # Write out initial config, if no config exists.
            if nosafe:
                break
            sleep(0.2)
    return data_dict


def __write_cfg_file(dictionary):
    global CONFIG_CACHE
    while True:
        try:
            # WRITE CACHE
            CONFIG_CACHE = dictionary
            # WRITE JSON CONFIG
            with open(CONFIG_PATH, 'w') as f:
                dump(dictionary, f)
            break
        except Exception as e:
            console_write("[CONFIGHANDLER] __write_cfg_file error {} (json): {}".format(CONFIG_PATH, e))
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
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
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


if "ConfigHandler" in __name__:
    __inject_default_conf()                     # Validate / update / create user config
    DEBUG_PRINT = cfgget('dbg')                 # Inject from user conf
    if not cfgget('pled'): PLED = None          # Turn off progressled if necesary

#################################################################
#                            DEMO                               #
#################################################################


def confighandler_demo():
    global DEBUG_PRINT, PLED
    __inject_default_conf()                     # Validate / update / create user config
    DEBUG_PRINT = cfgget('dbg')                 # Inject from user conf
    if not cfgget('pled'): PLED = None          # Turn off progressled if necesary

    cfgget_all()                                # Dump full config
    console_write("Write console msg ...")      # Test console write


if __name__ == "__main__":
    confighandler_demo()
