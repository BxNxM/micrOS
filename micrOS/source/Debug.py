import os
from time import localtime

try:
    from LogicalPins import physical_pin, pinmap_dump, detect_platform
except:
    detect_platform = None


#############################################
#       DEBUG PRINT + PROGRESS LED          #
#############################################


class DebugCfg:
    DEBUG = True        # DEBUG PRINT ON/OFF - SET FROM ConfigHandler
    PLED_STEP = None    # PROGRESS LED OBJECT - init in init_pled
    PLED_A = False      # ANALOG "BLINK" LED FEATURE - True when analog, false when colorwheel
    NEO_WHEEL = None    # NEOPIXEL (ws2812/esp32s3) color wheel object

    @staticmethod
    def init_pled():
        # CALL FROM ConfigHandler
        if detect_platform is None:
            # Check LogicalPins module loadable (robustness...)
            return
        micro_platform = detect_platform()
        if micro_platform == "tinypico":
            # Progress led for TinyPico
            DebugCfg._init_apa102()
        elif pinmap_dump('builtin')['builtin'] is not None:
            if micro_platform == "esp32s3":
                # Progress led for esp32s3
                DebugCfg._init_ws2812()
            else:
                # Progress led for esp32/etc
                DebugCfg._init_simple()

    @staticmethod
    def _init_simple():
        try:
            from machine import Pin
            # Progress led for esp32/etc
            led_obj = Pin(physical_pin('builtin'), Pin.OUT)
            # Set function callback for step function (simple led - blink)
            DebugCfg.PLED_STEP = lambda: led_obj.value(not led_obj.value())
            DebugCfg.PLED_A = True
        except Exception as e:
            errlog_add(f"[PLED] led error: {e}")

    @staticmethod
    def _init_apa102():
        try:
            from TinyPLed import init_APA102, step
            # Progress led for TinyPico
            init_APA102()
            # Set function callback for step function (apa102 - color wheel)
            DebugCfg.PLED_STEP = step
        except Exception as e:
            errlog_add(f"[PLED] apa102 error: {e}")

    @staticmethod
    def _init_ws2812():
        try:
            from machine import Pin
            from neopixel import NeoPixel
            neo_pin = Pin(physical_pin('builtin'))
            led_obj = NeoPixel(neo_pin, 1)
            DebugCfg.PLED_STEP = lambda: DebugCfg._step_ws2812(led_obj)
        except Exception as e:
            errlog_add(f"[PLED] ws2812 error: {e}")

    @staticmethod
    def _step_ws2812(led_obj):
        def __color_wheel():
            while True:
                yield 10, 0, 0
                yield 5, 5, 0
                yield 0, 10, 0
                yield 0, 5, 5
                yield 0, 0, 10
                yield 5, 0, 5
        if DebugCfg.NEO_WHEEL is None:
            DebugCfg.NEO_WHEEL = __color_wheel()
        led_obj[0] = DebugCfg.NEO_WHEEL.__next__()
        led_obj.write()

    @staticmethod
    def step():
        """
        DEBUG LED FEEDBACK
        - handle 3 types of builtin LEDs: analog, neopixel(ws2812), apa102
        - automatic selection based on board type + builtin logical pin number
        """
        try:
            if DebugCfg.PLED_STEP:
                DebugCfg.PLED_STEP()
                return DebugCfg.PLED_A      # Return analog (True) - "double blink"
            return False
        except Exception as e:
            errlog_add(f"[PLED] step error: {e}")
            return False


def console_write(msg):
    if DebugCfg.DEBUG:
        try:
            analog = DebugCfg.step()
            print(msg)
            if analog:
                DebugCfg.step()
        except Exception as e:
            errlog_add(f"[ERR] console_write: {e}")

#############################################
#        LOGGING WITH DATA ROTATION         #
#############################################


def logger(data, f_name, limit):
    """
    Create generic logger function
    - implements log line rotation
    - automatic time stump
    :param data: input string data to log
    :param f_name: file name to use
    :param limit: line limit for log rotation
    return write verdict - true / false
    INFO: hardcoded max data number = 30
    """
    def _logger(_data, _f_name, _limit, f_mode='r+'):
        _limit = 30 if _limit > 30 else _limit
        # [1] GET TIME STUMP
        ts_buff = [str(k) for k in localtime()]
        ts = ".".join(ts_buff[0:3]) + "-" + ":".join(ts_buff[3:6])
        # [2] OPEN FILE - WRITE DATA WITH TS
        with open(_f_name, f_mode) as f:
            _data = f"{ts} {_data}\n"
            # read file lines and filter by time stump chunks (hack for replace truncate)
            lines = [_l for _l in f.readlines() if '-' in _l and '.' in _l]
            # get file params
            lines_len = len(lines)
            lines.append(_data)
            f.seek(0)
            # line data rotate
            if lines_len >= _limit:
                lines = lines[-_limit:]
                lines_str = ''.join(lines)
            else:
                lines_str = ''.join(lines)
            # write file
            f.write(lines_str)

    # Run logger
    try:
        # There is file - append 'r+'
        _logger(data, f_name, limit)
    except:
        try:
            # There is no file - create 'a+'
            _logger(data, f_name, limit, 'a+')
        except:
            return False
    return True


def log_get(f_name, msgobj=None):
    """
    Get and stream (ver osocket/stdout) .log file's content and count "critical" errors
    - critical error tag in log line: [ERR]
    """
    err_cnt = 0
    try:
        with open(f_name, 'r') as f:
            eline = f.readline().strip()
            while eline:
                # GET error from log line (tag: [ERR])
                err_cnt += 1 if "[ERR]" in eline else 0
                # GIVE BACK .log file contents
                if msgobj is None:
                    console_write(eline)
                else:
                    msgobj(eline)
                eline = f.readline().strip()
    except:
        pass
    return err_cnt


#############################################
#               ERROR LOGGING               #
#############################################


def errlog_add(data):
    """
    :param data: msg string / data
    :return: is ok
    """
    f_name = 'err.log'
    return logger(data, f_name, limit=5)


def errlog_get(msgobj=None):
    f_name = 'err.log'
    errcnt = log_get(f_name, msgobj)
    # Return error number
    return errcnt


def errlog_clean(msgobj=None):
    to_del = [file for file in os.listdir() if file.endswith('.log')]
    for _del in to_del:
        del_msg = f" Delete: {_del}"
        if msgobj is None:
            console_write(del_msg)
        else:
            msgobj(del_msg)
        os.remove(_del)
