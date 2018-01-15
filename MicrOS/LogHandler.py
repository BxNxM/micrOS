# VERSION: 1.0
#################################################################
#         _____ __  __ _____   ____  _____ _______ _____        #
#        |_   _|  \/  |  __ \ / __ \|  __ \__   __/ ____|       #
#          | | | \  / | |__) | |  | | |__) | | | | (___         #
#          | | | |\/| |  ___/| |  | |  _  /  | |  \___ \        #
#         _| |_| |  | | |    | |__| | | \ \  | |  ____) |       #
#        |_____|_|  |_|_|     \____/|_|  \_\ |_| |_____/        #
#################################################################

import os
try:
    import progressled
except Exception as e:
    print("MICROPYTHON IMPORT ERROR - " + str(e))
try:
    import ConfigHandler
except Exception as e:
    print("MICROPYTHON IMPORT ERROR - " + str(e))
try:
    import commands
except Exception as e:
    print("MICROPYTHON IMPORT ERROR - " + str(e))

#################################################################
#          _____ _                _____ _____                   #
#         / ____| |        /\    / ____/ ____|                  #
#        | |    | |       /  \  | (___| (___                    #
#        | |    | |      / /\ \  \___ \\___ \                   #
#        | |____| |____ / ____ \ ____) |___) |                  #
#         \_____|______/_/    \_\_____/_____/                   #
#################################################################

class Logger(object):
    __instance = None
    def __new__(cls, name="logger", logpath="logs.log", log_limit=1000, autoclean=False):
        cls.logpath = logpath
        cls.log_limit = log_limit                                          # size of file, in bytes
        if cls.__instance == None:
            cls.__instance = object.__new__(cls)
            cls.__instance.name = name
            cls.__instance.autoclean = autoclean
            if cls.__instance.autoclean is True:
                cls.__instance.clean()
            else:
                cls.__instance.init_log()
            settings_msg = "Logger settings [OK]:\n\tlogpath - " + str(logpath) + "\n\tlog_limit - " + str(log_limit) + "\n\tautoclean - " + str(autoclean)
            cls.__instance.exception(settings_msg)
        return cls.__instance

    # INFO LOG - JUST TO CONSOLE
    def info(cls, msg):
       cls.sub_logger("[ info ]", msg, 0, isLight=True)

    # DEBUG LOG - TO CONSOLE AND FILE TOO
    def debug(cls, msg):
        log_limit = cls.log_limit
        cls.sub_logger("[ debug ]", msg, log_limit)

    # EXCEPTION (extended log size) LOG - TO CONSOLE AND FILE TOO
    def exception(cls, msg):
        log_limit = cls.log_limit + 500
        cls.sub_logger("[ !exception! ]", msg, log_limit)

    def sub_logger(cls, tag, msg, file_limit, isLight=False):
        cls.progressled()
        try:
            if isLight:
                title = "light call -- bytes - " + str(tag) + " - " + msg
            else:
                title = str(cls.log_size()) + "/" + str(cls.log_limit) +  " bytes - " + str(tag) + " - " + msg
            print("$stdio$> " + str(title))
            if cls.log_size() < file_limit:
                try:
                    with open(cls.logpath, 'a') as f:
                        f.write(str(title) + "\n")
                except Exception as e:
                    msg = str(tag) + " - " + str(e)
                    cls.exception(msg)
        except MemoryError as e:
            print("MEMORY ERROR: " + str(e))

    def clean(cls):
        if cls.isexits():
            os.remove(cls.logpath)
            cls.init_log()

    def printout(cls):
        log_content = ""
        if cls.isexits():
            try:
                with open(cls.logpath, 'r') as f:
                    log_content = f.read()
            except Exception as e:
                msg = "logger_printout exception: " + str(e)
                cls.exception(msg)
            finally:
                print(log_content)

    def init_log(cls):
        # IF CONFIGFILE IS NOT EXISTS
        if not cls.isexits():
            try:
                with open(cls.logpath, 'w') as f:
                    f.write("======= WELCOME LOGPY [bnm] =======\n")
            except Exception as e:
                msg = "logger.info exception: " + str(e)
                cls.exception(msg)

    # FILE CHECK - OS FUNCTIONS - DIFFERNET ON MICROPYTHON!!!
    def isexits(cls):
        is_exists = False
        try:
            # NORMAL PYTHON
            is_exists = os.path.isfile(cls.logpath)
        except:
            # MICROPYTHON
            files = os.listdir()
            if str(cls.logpath) in str(files):
                is_exists = True
        return is_exists

    # FILE CHACK - OS FUNCTION - DIFFERNET ON MICROPYTHON!!!
    def log_size(cls):
        try:
            # NORMAL PYTHON
            size = os.stat(cls.logpath).st_size
        except:
            # MICROPYTHON
            try:
                size = os.stat(cls.logpath)[6]  # size of file, in bytes
            except:
                if cls.isexits():
                    size = cls.log_limit + 100
                else:
                    size = 0
        return int(size)

    def progressled(cls):
        try:
            progressled.pled.toggle()
        except:
            pass

#################################################################################################################
#  _____ _   _  _____ _______       _   _ _______ _____       _______ ______                                    #
# |_   _| \ | |/ ____|__   __|/\   | \ | |__   __|_   _|   /\|__   __|  ____|                                   #
#   | | |  \| | (___    | |  /  \  |  \| |  | |    | |    /  \  | |  | |__                                      #
#   | | | . ` |\___ \   | | / /\ \ | . ` |  | |    | |   / /\ \ | |  |  __|                                     #
#  _| |_| |\  |____) |  | |/ ____ \| |\  |  | |   _| |_ / ____ \| |  | |____                                    #
# |_____|_| \_|_____/   |_/_/    \_\_| \_|  |_|  |_____/_/    \_\_|  |______| a singleton, return instance      #
#################################################################################################################

def config_instantiate():
    logger = None
    try:
        # CONFIG READ: if log limit string paramter(cmd)
        if str(ConfigHandler.cfg.get('log_limit')) == "auto_1/2":
            freedisk = commands.diskfree()
            limit = int(freedisk[0]/2)
        elif str(ConfigHandler.cfg.get('log_limit')) == "auto_1/3":
            freedisk = commands.diskfree()
            limit = int(freedisk[0]/3)
        elif str(ConfigHandler.cfg.get('log_limit')) == "auto_1/4":
            freedisk = commands.diskfree()
            limit = int(freedisk[0]/4)
        # if log limit is a number
        else:
            limit = int(ConfigHandler.cfg.get('log_limit'))
        # CONFIG READ: if log_boot_clean is True - when boot clean is on
        if str(ConfigHandler.cfg.get('log_boot_clean')) == "True":
            autoclean_reboot = True
        # CONFIG READ: if log_boot_clean is False - when boot clean is off
        else:
            autoclean_reboot = False
        # instantiates Logger class - with config parameters - singleton instance name is logger
        logger = Logger(log_limit=limit, autoclean=autoclean_reboot)
        logger.exception("~~~ LOGGER CONFIGURATED FROM CONFIG FILE...")
    except Exception as e:
        # instantiates Logger class - with default parameters - singleton instance name is logger
        logger = Logger()
        logger.exception("~~~ LOGGER RUNS WITH DEFAULT SETTINGS... - CONFIG exception: " + str(e))
    finally:
        return logger

#################################################################
#         __  __  ____  _____  _    _ _      ______             #
#        |  \/  |/ __ \|  __ \| |  | | |    |  ____|            #
#        | \  / | |  | | |  | | |  | | |    | |__               #
#        | |\/| | |  | | |  | | |  | | |    |  __|              #
#        | |  | | |__| | |__| | |__| | |____| |____             #
#        |_|  |_|\____/|_____/ \____/|______|______| IMPORT     #
#################################################################

if "LogHandler" in __name__:
    logger = config_instantiate()
#################################################################
#         _____  ______ __  __  ____                            #
#        |  __ \|  ____|  \/  |/ __ \                           #
#        | |  | | |__  | \  / | |  | |                          #
#        | |  | |  __| | |\/| | |  | |                          #
#        | |__| | |____| |  | | |__| |                          #
#        |_____/|______|_|  |_|\____/ and TEST                  #
#################################################################

if __name__ == "__main__":
    logger = config_instantiate()
    if logger is not None:
        logger.info("hello info")
        logger.debug("hello debug")
        logger.exception("hello exception")
        logger.printout()
    else:
        print("LOGGER instance is None! - ERROR")
