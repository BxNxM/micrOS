# VERSION: 1.0
#################################################################
#         _____ __  __ _____   ____  _____ _______ _____        #
#        |_   _|  \/  |  __ \ / __ \|  __ \__   __/ ____|       #
#          | | | \  / | |__) | |  | | |__) | | | | (___         #
#          | | | |\/| |  ___/| |  | |  _  /  | |  \___ \        #
#         _| |_| |  | | |    | |__| | | \ \  | |  ____) |       #
#        |_____|_|  |_|_|     \____/|_|  \_\ |_| |_____/        #
#################################################################
import json
try:
    import LogHandler
    print("[ MICROPYTHON MODULE LOAD ] - LOGHANDLER - from " + str(__name__))
except Exception as e:
    print("[ MICROPYTHON IMPORT ERROR ] - " + str(e)  + " - from " + str(__name__))
    LogHandler = None

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

    def __new__(cls, name="confighandler", cfg_path="node_config.json"):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
            cls.__instance.name = name
            cls.cfg_path = cfg_path
        return cls.__instance

    # EXTERNAL FUNCTIONS - GET VALUE
    def get(cls, key):
        config = cls.read_cfg_file()
        try:
            value = config[key]
        except:
            value = None
        return value

    # EXTERNAL FUNCTION - GET ALL
    def get_all(cls):
        config = cls.read_cfg_file()
        return config

    # EXTERNAL FUNCTION - PUT VALUE
    def put(cls, key, value):
        config = cls.read_cfg_file()
        config[key] = value
        cls.write_cfg_file(config)

    def write_cfg_file(cls, dictionary):
        try:
            with open(cls.cfg_path, 'w') as f:
                json.dump(dictionary, f, sort_keys=True, indent=2)
        except Exception as e:
            if LogHandler is not None:
                LogHandler.logger.exception("ConfigHandler.write_cfg_file write json: " + str(e))
            else:
                raise Exception("ConfigHandler.write_cfg_file write json: " + str(e))

    def read_cfg_file(cls):
        try:
            with open(cls.cfg_path, 'r') as f:
                data_dict = json.load(f)
        except:
            data_dict = {}
        return data_dict

#################################################################################################################
#  _____ _   _  _____ _______       _   _ _______ _____       _______ ______                                    #
# |_   _| \ | |/ ____|__   __|/\   | \ | |__   __|_   _|   /\|__   __|  ____|                                   #
#   | | |  \| | (___    | |  /  \  |  \| |  | |    | |    /  \  | |  | |__                                      #
#   | | | . ` |\___ \   | | / /\ \ | . ` |  | |    | |   / /\ \ | |  |  __|                                     #
#  _| |_| |\  |____) |  | |/ ____ \| |\  |  | |   _| |_ / ____ \| |  | |____                                    #
# |_____|_| \_|_____/   |_/_/    \_\_| \_|  |_|  |_____/_/    \_\_|  |______| a singleton, return instance      #
#################################################################################################################
#################################################################
#         __  __  ____  _____  _    _ _      ______             #
#        |  \/  |/ __ \|  __ \| |  | | |    |  ____|            #
#        | \  / | |  | | |  | | |  | | |    | |__               #
#        | |\/| | |  | | |  | | |  | | |    |  __|              #
#        | |  | | |__| | |__| | |__| | |____| |____             #
#        |_|  |_|\____/|_____/ \____/|______|______| IMPORT     #
#################################################################
if "ConfigHandler" == __name__:
    cfg = ConfigHandler()

#################################################################
#         _____  ______ __  __  ____                            #
#        |  __ \|  ____|  \/  |/ __ \                           #
#        | |  | | |__  | \  / | |  | |                          #
#        | |  | |  __| | |\/| | |  | |                          #
#        | |__| | |____| |  | | |__| |                          #
#        |_____/|______|_|  |_|\____/ and TEST                  #
#################################################################
if __name__ == "__main__":
    cfg = ConfigHandler()

    cfg.put("test1", "Test write (1)")
    cfg.put("test2", "Test Write (2)")
    cfg.put("test1", "Test write (3)")
    cfg.get("test1")

    print(cfg.get_all())
