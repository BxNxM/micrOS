# VERSION: 1.0
#################################################################
#         _____ __  __ _____   ____  _____ _______ _____        #
#        |_   _|  \/  |  __ \ / __ \|  __ \__   __/ ____|       #
#          | | | \  / | |__) | |  | | |__) | | | | (___         #
#          | | | |\/| |  ___/| |  | |  _  /  | |  \___ \        #
#         _| |_| |  | | |    | |__| | | \ \  | |  ____) |       #
#        |_____|_|  |_|_|     \____/|_|  \_\ |_| |_____/        #
#################################################################
import Console
try:
    import ujson as json
except Exception as e:
    Console.write("ujson module not found: " + str(e))
    import json

CONFIG_PATH="node_config.json"
DEFAULT_CONFIGURATION_TEMPLATE = {"sta_essid": "your_wifi_name",
                                  "sta_pwd": "your_wifi_passwd",
                                  "node_name": "slim01",
                                  "progressled": True,
                                  "nw_mode": "Unknown",
                                  "ap_passwd": "admin",
                                  "shell_timeout": 100}

#################################################################
#          _____ _                _____ _____                   #
#         / ____| |        /\    / ____/ ____|                  #
#        | |    | |       /  \  | (___| (___                    #
#        | |    | |      / /\ \  \___ \\___ \                   #
#        | |____| |____ / ____ \ ____) |___) |                  #
#         \_____|______/_/    \_\_____/_____/                   #
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
            Console.write("Get config value error: {}".format(e))
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
                Console.write("  {}: {}".format(key, value))
        else:
            Console.write("data_struct not dict: " + str(data_struct))

    def write_cfg_file(cls, dictionary):
        if not isinstance(dictionary, dict):
            Console.write("ConfigHandler.write_cfg_file - config data struct should be a dict!")
            return False
        try:
            with open(cls.cfg_path, 'w') as f:
                json.dump(dictionary, f)
            return True
        except Exception as e:
                Console.write("ConfigHandler.write_cfg_file error {} (json): {}".format(cls.cfg_path, e))
                return False

    def read_cfg_file(cls):
        try:
            with open(cls.cfg_path, 'r') as f:
                data_dict = json.load(f)
        except Exception as e:
            Console.write("ConfigHandler.read_cfg_file error {} (json): {}".format(cls.cfg_path, e))
            data_dict = {}
        return data_dict

    def inject_default_conf(cls, data_struct=None):
        if data_struct == None:
            data_struct = cls.cfg_template
        elif not isinstance(data_struct, dict):
            Console.write("inject_default_conf input data type must be dict")
            return
        data_dict = cls.read_cfg_file()
        data_struct.update(data_dict)
        try:
            if cls.write_cfg_file(data_struct):
                Console.write("Inject default data struct successful")
            else:
                Console.write("Inject default data struct failed")
        except Exception as e:
            Console.write(e)

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
            Console.write("Input value type error! {}".format(e))
            return None

#################################################################
#         __  __  ____  _____  _    _ _      ______             #
#        |  \/  |/ __ \|  __ \| |  | | |    |  ____|            #
#        | \  / | |  | | |  | | |  | | |    | |__               #
#        | |\/| | |  | | |  | | |  | | |    |  __|              #
#        | |  | | |__| | |__| | |__| | |____| |____             #
#        |_|  |_|\____/|_____/ \____/|______|______| IMPORT     #
#################################################################
if "ConfigHandler" in __name__:
    cfg = ConfigHandler()
    cfg.inject_default_conf(DEFAULT_CONFIGURATION_TEMPLATE)

#################################################################
#         _____  ______ __  __  ____                            #
#        |  __ \|  ____|  \/  |/ __ \                           #
#        | |  | | |__  | \  / | |  | |                          #
#        | |  | |  __| | |\/| | |  | |                          #
#        | |__| | |____| |  | | |__| |                          #
#        |_____/|______|_|  |_|\____/ and TEST                  #
#################################################################
def confighandler_demo():
    cfg = ConfigHandler()
    cfg.inject_default_conf(DEFAULT_CONFIGURATION_TEMPLATE)
    cfg.print_all()

if __name__ == "__main__":
    confighandler_demo()
