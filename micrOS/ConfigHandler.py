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
from machine import Pin
from LogicalPins import get_pin_on_platform_by_key
from os import remove
try:
    # TinyPICO progress led plugin
    import TinyPLed
except Exception as e:
    TinyPLed = None


class Data:
    # SET IT LATER FROM CONFIG
    DEBUG_PRINT = True
    CONFIG_CACHE = {}
    PLED = None
    # - micrOS config
    CONFIG_PATH = "node_config.json"

#################################################################
#                       MODULE CONFIG
#################################################################


def default_config():
    """
    micrOS "code" config.
    n/a default empty value (str)
    """
    default_configuration_template = {"version": "n/a",
                                      "auth": False,
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
                                      "cron": False,
                                      "crontasks": "n/a",
                                      "cronseq": 3000,
                                      "timirq": False,
                                      "timirqcbf": "n/a",
                                      "timirqseq": 3000,
                                      "irqmembuf": 1000,
                                      "extirq": False,
                                      "extirqcbf": "n/a",
                                      "extirqtrig": "n/a",
                                      "boothook": "n/a",
                                      "gmttime": +1,
                                      "boostmd": True,
                                      "irqmreq": 6000,
                                      "guimeta": "n/a",
                                      "cstmpmap": "n/a"}
    return default_configuration_template

#################################################################
#                     CONSOLE WRITE FUNCTIONS                   #
#################################################################


def progress_led_toggle_adaptor(func):
    def wrapper(*args, **kwargs):
        if TinyPLed is None:
            # Simple (built-in) progress led update
            if Data.PLED is not None: Data.PLED.value(not Data.PLED.value())
            output = func(*args, **kwargs)
            if Data.PLED is not None: Data.PLED.value(not Data.PLED.value())
            return output
        # TinyPICO (built-in) progress led update
        if Data.PLED is not None: TinyPLed.step()
        # Run function
        return func(*args, **kwargs)
    return wrapper


@progress_led_toggle_adaptor
def console_write(msg):
    if Data.DEBUG_PRINT:
        print(msg)


#################################################################
#                  CONFIGHANDLER  FUNCTIONS                     #
#################################################################


def cfgget(key):
    try:
        return read_cfg_file().get(key, None)
    except Exception as e:
        console_write("[CONFIGHANDLER] Get config value error: {}".format(e))
    return None


def cfgput(key, value, type_check=False):
    if cfgget(key) == value:
        return True
    try:
        if type_check:
            value = __type_handler(key, value)
        if value is not None:
            cfg_dict_buffer = read_cfg_file()
            cfg_dict_buffer[key] = value
            __write_cfg_file(cfg_dict_buffer)
            del cfg_dict_buffer, value
            return True
    except Exception:
        pass
    return False

#################################################################
#             CONFIGHANDLER  INTERNAL FUNCTIONS                 #
#################################################################


def read_cfg_file(nosafe=False):
    while True:
        try:
            if len(Data.CONFIG_CACHE) == 0:
                # READ JSON CONFIG
                with open(Data.CONFIG_PATH, 'r') as f:
                    Data.CONFIG_CACHE.update(load(f))
            break
        except Exception as e:
            console_write("[CONFIGHANDLER] read_cfg_file error {} (json): {}".format(Data.CONFIG_PATH, e))
            # Write out initial config, if no config exists.
            if nosafe:
                break
            sleep(0.2)
    # Return config cache
    return Data.CONFIG_CACHE


def __write_cfg_file(dictionary):
    # WRITE CACHE
    Data.CONFIG_CACHE.update(dictionary)
    while True:
        try:
            # WRITE JSON CONFIG
            with open(Data.CONFIG_PATH, 'w') as f:
                dump(dictionary, f)
            break
        except Exception as e:
            console_write("[CONFIGHANDLER] __write_cfg_file error {} (json): {}".format(Data.CONFIG_PATH, e))
        sleep(0.2)
    return True


def __inject_default_conf():
    # Load config and template
    conf = default_config()
    liveconf = read_cfg_file(nosafe=True)
    # Remove obsolete keys from conf
    try:
        remove('cleanup.pds')       # Try to remove cleanup.pds (cleanup indicator by micrOSloader)
        console_write("[CONFIGHANDLER] Purge obsolete keys")
        for key in (key for key in liveconf.keys() if key not in conf.keys()):
            liveconf.pop(key, None)
    except Exception:
        console_write("[CONFIGHANDLER] SKIP obsolete keys check (no cleanup.pds)")
    # Merge template to live conf
    conf.update(liveconf)
    # Run conf injection and store
    if conf['dbg']:
        console_write("[CONFIGHANDLER] inject config:\n{}".format(conf))
    try:
        # [LOOP] Only returns True
        __write_cfg_file(conf)
        console_write("[CONFIGHANDLER] Inject default conf struct successful")
    except Exception as e:
        console_write("[CONFIGHANDLER] Inject default conf struct failed: {}".format(e))
    finally:
        del conf


def __type_handler(key, value):
    value_in_cfg = cfgget(key)
    try:
        if isinstance(value_in_cfg, bool):
            del value_in_cfg
            if str(value).lower() == 'true':
                return True
            if str(value).lower() == 'false':
                return False
            raise Exception("__type_handler type handling error")
        if isinstance(value_in_cfg, str):
            del value_in_cfg
            return str(value)
        if isinstance(value_in_cfg, int):
            del value_in_cfg
            return int(value)
        if isinstance(value_in_cfg, float):
            del value_in_cfg
            return float(value)
    except Exception as e:
        console_write("Input value type error! {}".format(e))
    return None

#################################################################
#                       MODULE AUTO INIT                        #
#################################################################


if "ConfigHandler" in __name__:
    # [!!!] Validate / update / create user config
    __inject_default_conf()
    if not cfgget('dbg'): console_write("[micrOS] debug print was turned off")
    # [!!!] Init selected pinmap ('builtin' is the default key, 'cstmpmap' user LP data)
    if cfgget('cstmpmap') != 'n/a': get_pin_on_platform_by_key('builtin', cfgget('cstmpmap'))
    # SET plead and dbg based on config settings (inject user conf)
    if cfgget('pled'):
        if TinyPLed is None:
            # Progress led for esp8266/esp32/etc
            if get_pin_on_platform_by_key('builtin') is not None:
                Data.PLED = Pin(get_pin_on_platform_by_key('builtin'), Pin.OUT)
        else:
            # Progress led for TinyPico
            Data.PLED = TinyPLed.init_APA102()
    Data.DEBUG_PRINT = cfgget('dbg')

if __name__ == "__main__":
    __inject_default_conf()
