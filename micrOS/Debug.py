import os
from time import localtime
from machine import Pin
from LogicalPins import physical_pin


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
    PLED_OBJ = None         # PROGRESS LED OBJECT - init in init_pled

    @staticmethod
    def init_pled():
        # CALL FROM ConfigHandler
        if TinyPLed is None:
            if physical_pin('builtin') is not None:
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


def errlog_add(data, limit=10):
    """
    :param data: msg string / data
    :param limit: line limit to rotate
    :return: is ok
    """
    fname = 'err.log'

    def add_line(data, fname):
        with open(fname, 'a+') as f:
            buff = [str(k) for k in localtime()]
            ts = ".".join(buff[0:3]) + " " + ":".join(buff[3:6])
            try:
                f.write('{ts} {data}\n'.format(ts=ts, data=data))
            except:
                pass

    def logrotate(fname):
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
    add_line(data, fname)
    logrotate(fname)


def errlog_get(msgobj=None):
    errcnt = 0

    def stream_records(fname):
        cnt = 0
        try:
            with open(fname, 'r') as f:
                eline = f.readline().strip()
                while eline:
                    cnt += 1
                    if msgobj is None:
                        console_write(eline)
                    else:
                        msgobj(eline)
                    eline = f.readline().strip()
        except:
            pass
        return cnt
    to_list = [file for file in os.listdir() if file.endswith('.log')]
    for log in to_list:
        errcnt += stream_records(log)
    return errcnt


def errlog_clean():
    to_del = [file for file in os.listdir() if file.endswith('.log')]
    for _del in to_del:
        os.remove(_del)
