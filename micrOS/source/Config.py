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
from re import search
from json import load, dump
from utime import sleep
from Debug import DebugCfg, console_write, syslog
from Files import OSPath, path_join, is_file
from uos import remove, rename
try:
    from microIO import set_pinmap
except:
    syslog("[ERR] microIO import: set_pinmap")
    set_pinmap = None


class Config:
    """
    Config class for managing configuration data.
    """
    __slots__ = (
        "version", "auth", "staessid", "stapwd", "devfid", "appwd", "dbg", "nwmd",
        "hwuid", "soctout", "socport", "webui", "webui_max_con", "devip", "cron",
        "crontasks", "timirq", "timirqcbf", "timirqseq", "irq1", "irq1_cbf",
        "irq1_trig", "irq2", "irq2_cbf", "irq2_trig", "irq3", "irq3_cbf", "irq3_trig",
        "irq4", "irq4_cbf", "irq4_trig", "irq_prell_ms", "boothook", "aioqueue",
        "utc", "boostmd", "guimeta", "cstmpmap", "espnow", "ha")

    CONFIG_NAME = "node_config.json"
    CONFIG_PATH = path_join(OSPath.CONFIG, CONFIG_NAME)
    INSTANCE = None
    OFFLOADED_VALUE = "..."

    # [CONFIG] Configuration parameters
    def __init__(self):
        # [System]
        self.devfid = "node01"      # Device Unique Name
        self.appwd = "ADmin123"     # Device password / webrepl / AP password
        self.boothook = "n/a"       # Boot tasks
        self.aioqueue = 5           # Maximum number of tasks
        self.boostmd = True         # Boost mode: High CPU setup
        self.cstmpmap = "n/a"       # Custom pin mapping IO/Individual tags
        self.ha = True              # High Availability feature: STA connect. monitoring (3min) and WDT (30sec)
        self.dbg = True             # Debug console prints + Built-In LED flashing while processing
        self.version = "n/a"        # Metadata
        self.hwuid = "n/a"          # Metadata
        self.guimeta = "..."        # Metadata - client/app GUI (offloaded key)
        # [Network]
        self.nwmd = "STA"           # Network mode: STA / AP
        self.staessid = "your_wifi_name"
        self.stapwd = "your_wifi_passwd"
        self.utc = +60
        self.soctout = 30
        self.socport = 9008
        self.devip = "n/a"
        self.espnow = False         # Enable Intercon ESPNow protocol
        self.auth = False           # Enable Shell/Web auth and module autoload protection
        # -- WebServer + RestAPI - MIN SYSTEM RAM requirement <200 kb
        self.webui = False
        self.webui_max_con = 3
        # [Interrupts]
        # -- Timer 0
        self.timirq = False
        self.timirqcbf = "n/a"
        self.timirqseq = 1000
        # -- Timer 1
        self.cron = False
        self.crontasks = "n/a"
        # -- Event "button" - external
        self.irq1 = False
        self.irq1_cbf = "n/a"
        self.irq1_trig = "n/a"
        self.irq2 = False
        self.irq2_cbf = "n/a"
        self.irq2_trig = "n/a"
        self.irq3 = False
        self.irq3_cbf = "n/a"
        self.irq3_trig = "n/a"
        self.irq4 = False
        self.irq4_cbf = "n/a"
        self.irq4_trig = "n/a"
        self.irq_prell_ms = 300

    def get(self, key, default=None):
        if not type(self).keys(key):
            return default
        return getattr(self, key)

    def set(self, key, value):
        if type(self).keys(key):
            setattr(self, key, value)

    @classmethod
    def keys(cls, key=None):
        if key is None:
            return cls.__slots__
        return key in cls.__slots__

    def items(self):
        for key in type(self).__slots__:
            yield key, getattr(self, key)

    # [CONFIG] ---------------------------

    @classmethod
    def init(cls):
        if cls.INSTANCE is None:
            cls.INSTANCE = cls()
        # Migrate config from / to /config
        if is_file(cls.CONFIG_NAME):
            console_write(f"[CONF] Migrate {cls.CONFIG_NAME} to {cls.CONFIG_PATH}")
            rename(cls.CONFIG_NAME, cls.CONFIG_PATH)
        # Inject user config into template
        cls._inject_default_conf()
        # [!!!] Init selected pinmap - default pinmap calculated by platform
        if callable(set_pinmap):
            try:
                pinmap = set_pinmap(cls.INSTANCE.get('cstmpmap'))
                console_write(f"[PIN MAP] {pinmap}")
            except Exception as e:
                console_write(f"\n[PIN MAP] !!! SETUP ERROR !!!: {e}\n")
        # SET dbg based on config settings (inject user conf)
        DebugCfg.DEBUG = cls.INSTANCE.get('dbg')
        if DebugCfg.DEBUG:
            # if debug ON, set progress led
            DebugCfg.init_pled()
        else:
            # Show info message - dbg OFF
            print("[micrOS] debug print - turned off")

    @classmethod
    def _inject_default_conf(cls):
        # Load config and template
        liveconf = cls.read_cfg_file(nosafe=True)
        _persist = False
        # Remove obsolete keys from conf
        try:
            remove('.cleanup')       # Try to remove .cleanup (cleanup indicator by micrOSloader)
            console_write("[CONF] Purge obsolete keys")
            for key in tuple(liveconf):
                if key not in cls.__slots__:
                    liveconf.pop(key, None)
                    _persist = True
        except Exception:
            console_write("[CONF] SKIP obsolete keys check (no .cleanup)")
        # Merge template to live conf
        for key, value in liveconf.items():
            cls.INSTANCE.set(key, value)
        console_write("[CONF] User config injection done")
        try:
            if not _persist:
                for key in cls.__slots__:
                    if key not in liveconf:
                        _persist = True
                        break
            if _persist:
                # Only persist when migration cleanup removed keys or defaults are missing from the file.
                cls.write_cfg_file()
                console_write("[CONF] Save conf successful")
        except Exception as e:
            syslog(f"[ERR] Save (__inject) conf failed: {e}")
        finally:
            del liveconf

    @staticmethod
    def read_cfg_file(nosafe=False):
        conf = {}
        while True:
            try:
                with open(Config.CONFIG_PATH, 'r') as f:
                    conf = load(f)
                break
            except Exception as e:
                console_write(f"[CONF] read_cfg_file error {conf} (json): {e}")
                # Write out initial config, if no config exists.
                if nosafe:
                    break
                sleep(0.2)
                syslog(f'[ERR] read_cfg_file error: {e}')
        # Return config cache
        return conf

    @staticmethod
    def write_cfg_file():
        while True:
            try:
                # WRITE JSON CONFIG
                with open(Config.CONFIG_PATH, 'w') as f:
                    dump({key: value for key, value in Config.INSTANCE.items()}, f)
                break
            except Exception as e:
                syslog(f'[ERR] write_cfg_file {Config.CONFIG_PATH} (json): {e}')
            sleep(0.2)
        return True

    @staticmethod
    def type_handler(key, value):
        value_in_cfg = Config.INSTANCE.get(key)
        try:
            if isinstance(value_in_cfg, bool):
                if str(value).lower() == 'true':
                    return True
                if str(value).lower() == 'false':
                    return False
                raise Exception("type_handler type handling error")
            if isinstance(value_in_cfg, str):
                return str(value)
            if isinstance(value_in_cfg, int):
                return int(value)
            if isinstance(value_in_cfg, float):
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
        offloaded_key = path_join(OSPath.CONFIG, f'.{key}.key')
        if isinstance(value, str) and Config.keys(key):
            try:
                with open(offloaded_key, 'w') as f:
                    f.write(value)
                return True
            except Exception:
                return False
        # Read str value from file
        try:
            with open(offloaded_key, 'r') as f:
                return f.read().strip()
        except Exception:
            # Return default value if key not exists
            return 'n/a'

    @staticmethod
    def validate_pwd(password):
        """
        Validate appwd parameter
        - webrepl password
        - micrOS auth password (Shell/WebCli)
        - wifi access point password
        """
        # Check password rules
        if 4 <= len(password) <= 9:
            if search(r"[A-Z]", password) and search(r"[a-z]", password):
                if search(r"\d", password):
                    return True, ''
        return False, 'Password must include [0-9] both [a-z][A-Z] and length between 4-9 char.'


#################################################################
#                  CONFIGHANDLER  FUNCTIONS                     #
#################################################################


def cfgget(key=None):
    if key is None:
        return Config.INSTANCE
    try:
        val = Config.INSTANCE.get(key)
        if val == Config.OFFLOADED_VALUE:
            # Handle special "offloaded" keys
            return Config.disk_keys(key)
        return val
    except Exception as e:
        syslog(f'[ERR] cfgget {key} error: {e}')
    return None

def cfgput(key, value, type_check=False):
    if key == 'appwd':
        is_valid, verdict = Config.validate_pwd(value)
        if not is_valid:
            raise Exception(verdict)
    # Handle special "offloaded" keys
    cache_value = Config.INSTANCE.get(key)
    if cache_value == Config.OFFLOADED_VALUE:
        return Config.disk_keys(key, value)
    # Handle regular keys
    if cache_value == value:
        return True
    try:
        if type_check:
            value = Config.type_handler(key, value)
        # value type error or deny "offloaded" key's value ...
        if value is None or str(value) == Config.OFFLOADED_VALUE:
            return False
        if not Config.keys(key):
            return False
        Config.INSTANCE.set(key, value)
        Config.write_cfg_file()
        del value
        return True
    except Exception as e:
        syslog(f'[ERR] cfgput {key} error: {e}')
        return False

#################################################################
#                       MODULE AUTO INIT                        #
#################################################################

# [!!!] Validate / update / create user config + sidecar functions
Config.init()
