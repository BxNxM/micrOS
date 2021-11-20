from machine import Pin
from LogicalPins import physical_pin


#############################################
#       DEBUG PRINT + PROGRESS LED          #
#############################################


class DebugCfg:
    DEBUG = True        # DEBUG PRINT ON/OFF - SET FROM ConfigHandler
    PLED = None         # PROGRESS LED OBJECT - init in init_pled

    @staticmethod
    def init_pled():
        # CALL FROM ConfigHandler
        if physical_pin('builtin') is not None:
            # Progress led for esp8266/esp32/etc
            DebugCfg.PLED = Pin(physical_pin('builtin'), Pin.OUT)


def console_write(msg):
    if DebugCfg.PLED is not None:
        # Simple (built-in) progress led update
        DebugCfg.PLED.value(not DebugCfg.PLED.value())
        if DebugCfg.DEBUG:
            print(msg)
        DebugCfg.PLED.value(not DebugCfg.PLED.value())
        return
    if DebugCfg.DEBUG:
        print(msg)
    return
