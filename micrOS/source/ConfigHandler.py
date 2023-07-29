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
from utime import sleep
from json import load, dump
from os import remove
from Debug import DebugCfg, console_write, errlog_add
try:
    from LogicalPins import set_pinmap
except:
    errlog_add("[ERR] LogicalPins import: set_pinmap")
    set_pinmap = None


class Data:
    # micrOS config path
    CONFIG_PATH = "node_config.json"
    CONFIG_CACHE = {"version": "n/a",
                    "auth": False,
                    "staessid": "your_wifi_name",
                    "stapwd": "your_wifi_passwd",
                    "devfid": "node01",
                    "appwd": "ADmin123",
                    "dbg": True,
                    "nwmd": "STA",
                    "hwuid": "n/a",
                    "soctout": 100,
                    "socport": 9008,
                    "devip": "n/a",
                    "cron": False,
                    "crontasks": "n/a",
                    "timirq": False,
                    "timirqcbf": "n/a",
                    "timirqseq": 1000,
                    "irq1": False,
                    "irq1_cbf": "n/a",
                    "irq1_trig": "n/a",
                    "irq2": False,
                    "irq2_cbf": "n/a",
                    "irq2_trig": "n/a",
                    "irq3": False,
                    "irq3_cbf": "n/a",
                    "irq3_trig": "n/a",
                    "irq4": False,
                    "irq4_cbf": "n/a",
                    "irq4_trig": "n/a",
                    "irq_prell_ms": 300,
                    "boothook": "n/a",
                    "aioqueue": 3,
                    "utc": +60,
                    "boostmd": True,
                    "guimeta": "...",     # special "offloaded" key indicator
                    "cstmpmap": "n/a",
                    "telegram": "n/a"}    # telegram bot token

    @staticmethod
    def init():
        # Inject user config into template
        Data.__inject_default_conf()
        # [!!!] Init selected pinmap - default pinmap calculated by platform
        if set_pinmap is not None:
            pinmap = set_pinmap(Data.CONFIG_CACHE['cstmpmap'])
            console_write(f"[PIN MAP] {pinmap}")
        # SET dbg based on config settings (inject user conf)
        DebugCfg.DEBUG = cfgget('dbg')
        if Data.CONFIG_CACHE['dbg']:
            # if debug ON, set progress led
            DebugCfg.init_pled()
        else:
            # Show info message - dbg OFF
            console_write("[micrOS] debug print - turned off")


    @staticmethod
    def __inject_default_conf():
        # Load config and template
        liveconf = Data.read_cfg_file(nosafe=True)
        # Remove obsolete keys from conf
        try:
            remove('cleanup.pds')       # Try to remove cleanup.pds (cleanup indicator by micrOSloader)
            console_write("[CONF] Purge obsolete keys")
            for key in (key for key in liveconf.keys() if key not in Data.CONFIG_CACHE.keys()):
                liveconf.pop(key, None)
            # TODO: dynamic ... key in new config - re-store value in offloaded mode.
        except Exception:
            console_write("[CONF] SKIP obsolete keys check (no cleanup.pds)")
        # Merge template to live conf (store active conf in Data.CONFIG_CACHE)
        Data.CONFIG_CACHE.update(liveconf)
        console_write("[CONF] User config injection done")
        try:
            # [LOOP] Only returns True
            Data.write_cfg_file()
            console_write("[CONF] Save conf struct successful")
        except Exception as e:
            console_write(f"[CONF] Save conf struct failed: {e}")
            errlog_add(f"[ERR] __inject_default_conf error: {e}")
        finally:
            del liveconf

    @staticmethod
    def read_cfg_file(nosafe=False):
        conf = {}
        while True:
            try:
                with open(Data.CONFIG_PATH, 'r') as f:
                    conf = load(f)
                break
            except Exception as e:
                console_write(f"[CONF] read_cfg_file error {conf} (json): {e}")
                # Write out initial config, if no config exists.
                if nosafe:
                    break
                sleep(0.2)
                errlog_add(f'[ERR] read_cfg_file error: {e}')
        # Return config cache
        return conf

    @staticmethod
    def write_cfg_file():
        while True:
            try:
                # WRITE JSON CONFIG
                with open(Data.CONFIG_PATH, 'w') as f:
                    dump(Data.CONFIG_CACHE, f)
                break
            except Exception as e:
                console_write(f"[CONF] __write_cfg_file error {Data.CONFIG_PATH} (json): {e}")
                errlog_add(f'[ERR] write_cfg_file error: {e}')
            sleep(0.2)
        return True

    @staticmethod
    def type_handler(key, value):
        value_in_cfg = Data.CONFIG_CACHE[key]
        try:
            if isinstance(value_in_cfg, bool):
                del value_in_cfg
                if str(value).lower() == 'true':
                    return True
                if str(value).lower() == 'false':
                    return False
                raise Exception("type_handler type handling error")
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
            console_write(f"Input value type error! {e}")
        return None

    @staticmethod
    def disk_keys(key, value=None):
        """
        Store/Restore (long) str value in/from separate file based on key
        These kind of parameters are not cached in memory
        """
        # Write str value to file
        if isinstance(value, str) and key in Data.CONFIG_CACHE.keys():
            try:
                with open(f'.{key}.key', 'w') as f:
                    f.write(value)
                return True
            except Exception:
                return False
        # Read str value from file
        try:
            with open(f'.{key}.key', 'r') as f:
                return f.read().strip()
        except Exception:
            # Return default value if key not exists
            return 'n/a'


#################################################################
#                  CONFIGHANDLER  FUNCTIONS                     #
#################################################################


def cfgget(key=None):
    if key is None:
        return Data.CONFIG_CACHE
    try:
        val = Data.CONFIG_CACHE.get(key, None)
        if val == '...':
            # Handle special "offloaded" keys
            return Data.disk_keys(key)
        return val
    except Exception as e:
        console_write(f"[CONF] Get config value error: {e}")
        errlog_add(f'[ERR] cfgget {key} error: {e}')
    return None


def cfgput(key, value, type_check=False):
    # Handle special "offloaded" keys
    if str(Data.CONFIG_CACHE.get(key, None)) == '...':
        return Data.disk_keys(key, value)
    # Handle regular keys
    if Data.CONFIG_CACHE[key] == value:
        return True
    try:
        if type_check:
            value = Data.type_handler(key, value)
        # value type error or deny "offloaded" key's value ...
        if value is None or str(value) == '...':
            return False
        Data.CONFIG_CACHE[key] = value
        Data.write_cfg_file()
        del value
        return True
    except Exception as e:
        errlog_add(f'[ERR] cfgput {key} error: {e}')
        return False

#################################################################
#                       MODULE AUTO INIT                        #
#################################################################


# [!!!] Validate / update / create user config + sidecar functions
Data.init()
