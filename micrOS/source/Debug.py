import os
from time import localtime
from machine import Pin

try:
    from LogicalPins import physical_pin, pinmap_dump
except:
    physical_pin = None

try:
    # TinyPICO progress led plugin
    import TinyPLed
except Exception as e:
    TinyPLed = None


#############################################
#       DEBUG PRINT + PROGRESS LED          #
#############################################


class DebugCfg:
    DEBUG = True        # DEBUG PRINT ON/OFF - SET FROM ConfigHandler
    PLED_OBJ = None     # PROGRESS LED OBJECT - init in init_pled

    @staticmethod
    def init_pled():
        # CALL FROM ConfigHandler
        if TinyPLed is None:
            if physical_pin is not None and pinmap_dump('builtin')['builtin'] is not None:
                # Progress led for esp8266/esp32/etc
                DebugCfg.PLED_OBJ = Pin(physical_pin('builtin'), Pin.OUT)
        else:
            # Progress led for TinyPico
            DebugCfg.PLED_OBJ = TinyPLed.init_APA102()


def console_write(msg):
    if DebugCfg.DEBUG:
        if isinstance(DebugCfg.PLED_OBJ, Pin):
            # Simple (built-in) progress led update
            DebugCfg.PLED_OBJ.value(not DebugCfg.PLED_OBJ.value())
            print(msg)
            DebugCfg.PLED_OBJ.value(not DebugCfg.PLED_OBJ.value())
            return
        # TinyPICO (built-in) progress led update
        print(msg)
        if TinyPLed is None or DebugCfg.PLED_OBJ is None:
            return
        TinyPLed.step()


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
            _data = "{} {}\n".format(ts, _data)
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
    return logger(data, f_name, limit=8)


def errlog_get(msgobj=None):
    f_name = 'err.log'
    errcnt = log_get(f_name, msgobj)
    # Return error number
    return errcnt


def errlog_clean(msgobj=None):
    to_del = [file for file in os.listdir() if file.endswith('.log')]
    for _del in to_del:
        del_msg = " Delete: {}".format(_del)
        if msgobj is None:
            console_write(del_msg)
        else:
            msgobj(del_msg)
        os.remove(_del)
