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
    IO_USE_DICT = {}


def detect_platform():
    """
    Unified platform detection
    """
    if 'esp32' in platform:
        from os import uname
        if 'tinypico' in str(uname()[4]).lower():
            return 'tinypico'   # tinypico - esp32
        return 'esp32'          # esp32
    return platform             # esp8266 something else


def set_pinmap(lpsname=None):
    """
    Select pin map on device
    - by input name like: my_pinmap -> LP_my_pinmap.mpy
    - by platform detection, like: esp32 -> LM_esp32.mpy
    """
    # SELECT LOOKUP TABLE BASED ON PLATFORM / User input
    if isinstance(lpsname, str) and lpsname != 'n/a':
        if "LP_{}".format(lpsname) in [lp.split('.')[0] for lp in dir() if lp.startswith('LP_')]:
            PinMap.MAPPING_LUT = lpsname
            return PinMap.MAPPING_LUT
    PinMap.MAPPING_LUT = detect_platform()
    return PinMap.MAPPING_LUT


def physical_pin(key):
    """
    key - resolve pin number by logical name (like: switch_1)
    This function implements protected IO allocation (overload protection)
     for protected LM functions (IO-booking)
    """
    # Get pin number on platform by pin key aka logical pin
    pin_num = __resolve_pin_number(key)
    # Check pin is already used
    if pin_num in PinMap.IO_USE_DICT.keys():
        key_cache = PinMap.IO_USE_DICT[pin_num]
        if key_cache == key:
            print("[io] ReInit pin: {}:{}".format(key_cache, pin_num))
            return pin_num
        msg = "[io] Pin {} is busy: {}:{}".format(key, key_cache, pin_num)
        raise Exception(msg)
    # key: pin number, value: pin key (alias)
    PinMap.IO_USE_DICT[pin_num] = key
    print("[io] Init pin: {}:{}".format(key, pin_num))
    return pin_num


def get_pinmap():
    """
    Debug info function to get active pinmap and booked IO-s
    """
    return {'map': PinMap.MAPPING_LUT, 'booked': PinMap.IO_USE_DICT}


def pinmap_dump(keys):
    """
    keys: one or list of pin names (like: switch_1) to resolve physical pin number
    Gives information where to connect the selected periphery to control
    DO NOT USE RETURNED PIN NUMBERS FOR FUNC ALLOCATION IN LMs!!!
    - USE: physical_pin function for protected IO allocation (overload protection)
    """
    if isinstance(keys, str):
        try:
            num = __resolve_pin_number(keys)
        except:
            num = None
        return {keys: num}
    pins_cache = {}
    for pin_name in keys:
        try:
            num = __resolve_pin_number(pin_name)
        except:
            num = None
        pins_cache[pin_name] = num
    return pins_cache


def __resolve_pin_number(key):
    """
    Dynamic const lookup table handling by var name
    """
    # GET MODULE VARIABLE: SELECTED LOGICAL PIN ON BOARD
    try:
        # LOAD LOOKUP TABLE
        exec('import LP_{}'.format(PinMap.MAPPING_LUT))
        # GET KEY PARAM VALUE
        out = eval('LP_{}.{}'.format(PinMap.MAPPING_LUT, key))
        # Workaround to support normal python (tuple output), micropython (exact output - int)
        return int(out[0]) if isinstance(out, tuple) else out
    except Exception as e:
        msg = "[io-resolve] error: {}".format(e)
        print(msg)
        raise Exception(msg)
