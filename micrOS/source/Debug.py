import os
from time import localtime
from machine import Pin

try:
    from LogicalPins import physical_pin
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
            if physical_pin is not None and physical_pin('builtin') is not None:
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
#               ERROR LOGGING               #
#############################################


def errlog_add(data, limit=12):
    """
    :param data: msg string / data
    :param limit: line limit to rotate
    :return: is ok
    """
    fname = 'err.log'

    # ADD LINE TO LOG
    with open(fname, 'a+') as f:
        buff = [str(k) for k in localtime()]
        ts = ".".join(buff[0:3]) + " " + ":".join(buff[3:6])
        try:
            f.write('{ts} {data}\n'.format(ts=ts, data=data))
        except:
            pass

    # LOG ROTATE
    try:
        with open(fname) as f:
            flen = sum(1 for _ in f)
    except:
        flen = 0
    if flen >= int(limit / 2):
        try:
            # Rotate log
            with open(fname, 'r') as f:
                with open('{}.pre.log'.format(fname.split('.')[0]), 'w') as ff:
                    l = f.readline()
                    while l:
                        ff.write(l)
                        l = f.readline()
            os.remove(fname)
        except Exception as e:
            print("LogRotate error: {}".format(e))


def errlog_get(msgobj=None):
    errcnt = 0

    def stream_records(fname):
        """
        Get and stream (ver osocket/stdout) .log file's content and count "critical" errors
        - critical error tag in log line: [ERR]
        """
        err_cnt = 0
        try:
            with open(fname, 'r') as f:
                eline = f.readline().strip()
                while eline:
                    # GET error from log line (tag: [ERR])
                    if "[ERR]" in eline:
                        err_cnt += 1
                    # GIVE BACK .log file contents
                    if msgobj is None:
                        console_write(eline)
                    else:
                        msgobj(eline)
                    eline = f.readline().strip()
        except:
            pass
        return err_cnt

    # List all .log files on the board
    to_list = [file for file in os.listdir() if file.endswith('.log')]
    for log in to_list:
        # Get specific .log file contact
        errcnt += stream_records(log)
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
