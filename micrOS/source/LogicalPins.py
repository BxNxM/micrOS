"""
Module is responsible for board independent
input/output handling dedicated to micrOS framework.
- Hardware based pinout handling

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                           IMPORTS                             #
#################################################################
from sys import platform

#################################################################
#                        GPI/O ON DEVICE                        #
#################################################################


# Set automatically at the first time from ConfigHandler or sys.platform
class PinMap:
    MAPPING_LUT = None


def detect_platform():
    if 'esp32' in platform:
        from os import uname
        if 'tinypico' in str(uname()[4]).lower():
            return 'tinypico'   # tinypico - esp32
        return 'esp32'          # esp32
    return platform             # esp8266 something else


def set_pinmap(lpsname=None):
    # SELECT LOOKUP TABLE BASED ON PLATFORM / User input
    if isinstance(lpsname, str) and lpsname != 'n/a':
        if "LP_{}".format(lpsname) in [lp.split('.')[0] for lp in dir() if lp.startswith('LP_')]:
            PinMap.MAPPING_LUT = lpsname
            return PinMap.MAPPING_LUT
    PinMap.MAPPING_LUT = detect_platform()
    return PinMap.MAPPING_LUT


def get_pinmap():
    # Get active pin mapping
    return PinMap.MAPPING_LUT


def physical_pin(key):
    # GET MODULE VARIABLE: SELECTED LOGICAL PIN ON BOARD
    try:
        # LOAD LOOKUP TABLE
        exec('import LP_{}'.format(PinMap.MAPPING_LUT))
        # GET KEY PARAM VALUE
        return eval('LP_{}.{}'.format(PinMap.MAPPING_LUT, key))
    except Exception as e:
        #errlog_add("physical_pin error: missing key: {}: {}".format(key, e))
        return None
