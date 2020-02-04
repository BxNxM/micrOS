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
#                      CONFIGHANDLER  CLASS                     #
#################################################################
class ConfigHandler(object):
    __instance = None

    def __new__(cls, name="confighandler", cfg_path=CONFIG_PATH, cfg_template=DEFAULT_CONFIGURATION_TEMPLATE):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
            cls.__instance.name = name
            cls.cfg_path = cfg_path
            cls.cfg_template = cfg_template
        return cls.__instance

    # EXTERNAL FUNCTIONS - GET VALUE
    def get(cls, key):
        try:
            return cls.read_cfg_file().get(key, None)
        except Exception as e:
            console_write("Get config value error: {}".format(e))
        return None

    # EXTERNAL FUNCTION - PUT VALUE
    def put(cls, key, value):
        ret_status = False
        config = cls.read_cfg_file()
        try:
            value = cls.value_type_handler(key, value)
            if value is not None:
                config[key] = value
                cls.write_cfg_file(config)
                ret_status = True
        except:
            pass
        return ret_status

    # EXTERNAL FUNCTION - GET ALL
    def get_all(cls):
        config = cls.read_cfg_file()
        return config

    def print_all(cls):
        data_struct = dict(cls.read_cfg_file())
        if isinstance(data_struct, dict):
            for key, value in data_struct.items():
                console_write("  {}: {}".format(key, value))
        else:
            console_write("data_struct not dict: " + str(data_struct))

    def write_cfg_file(cls, dictionary):
        if not isinstance(dictionary, dict):
            console_write("ConfigHandler.write_cfg_file - config data struct should be a dict!")
            return False
        try:
            with open(cls.cfg_path, 'w') as f:
                dump(dictionary, f)
            return True
        except Exception as e:
                console_write("ConfigHandler.write_cfg_file error {} (json): {}".format(cls.cfg_path, e))
                return False

    def read_cfg_file(cls):
        try:
            with open(cls.cfg_path, 'r') as f:
                data_dict = load(f)
        except Exception as e:
            console_write("ConfigHandler.read_cfg_file error {} (json): {}".format(cls.cfg_path, e))
            data_dict = {}
        return data_dict

    def inject_default_conf(cls, data_struct=None):
        if data_struct == None:
            data_struct = cls.cfg_template
        elif not isinstance(data_struct, dict):
            console_write("inject_default_conf input data type must be dict")
            return
        data_dict = cls.read_cfg_file()
        data_struct.update(data_dict)
        try:
            if cls.write_cfg_file(data_struct):
                console_write("[CONFIGHANDLER] Inject default data struct successful")
            else:
                console_write("[CONFIGHANDLER] Inject default data struct failed")
        except Exception as e:
            console_write(e)

    def value_type_handler(cls, key, value):
        value_in_cfg = cls.get(key)
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
def init_module():
    global PLED_STAT, DEBUG_PRINT
    cfg = ConfigHandler()
    cfg.inject_default_conf(DEFAULT_CONFIGURATION_TEMPLATE)
    try:
        PLED_STAT = cfg.get("pled")
        DEBUG_PRINT = cfg.get("dbg")
    except Exception as e:
        print(e)
        DEBUG_PRINT = False
    return cfg

if "ConfigHandler" in __name__:
    cfg = init_module()

#################################################################
#         _____  ______ __  __  ____                            #
#        |  __ \|  ____|  \/  |/ __ \                           #
#        | |  | | |__  | \  / | |  | |                          #
#        | |  | |  __| | |\/| | |  | |                          #
#        | |__| | |____| |  | | |__| |                          #
#        |_____/|______|_|  |_|\____/ and TEST                  #
#################################################################
def confighandler_demo():
    cfg = init_module()
    cfg.print_all()
    console_write("Write console msg ...")

if __name__ == "__main__":
    confighandler_demo()
