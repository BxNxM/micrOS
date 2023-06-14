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
    MAPPING_LUT = None      # SELECTED STATIC PIN LUT (CUSTOM/PLATFORM)
    MAPPING = {}            # USER CUSTOM KEY MAPPING
    IO_USE_DICT = {}        # USED PIN ALLOCATION + OVERBOOK PROTECTION


def detect_platform():
    """
    Unified platform detection for micrOS
    """
    if 'esp32' in platform:
        from os import uname
        board = uname()[-1]
        if 'tinypico' in str(board).lower():
            return 'tinypico'    # esp32 family - tinypico
        if 'esp32s2' in str(board).lower():
            return 'esp32s2'     # esp32 family - esp32S2
        if 'esp32s3' in str(board).lower():
            return 'esp32s3'     # esp32 family - esp32s2 (octal spiram)
        return 'esp32'           # esp32 family - general
    return platform              # esp8266 or something else


def set_pinmap(map_data=None):
    """
    Select pin map on device (init from ConfigHandler)
    - map_data: default None (n/a), platform detection, like: esp32 -> LP_esp32.mpy
    - map_data: string input, like: my_pinmap -> LP_my_pinmap.mpy
    Parse map_data use cases:
        u.c.1: n/a or None                  - default - platform detection
        u.c.2: dht:10; neop:15              - default + manual overwrite pins
        u.c.3: esp32; dht:10; neop:15       - selected LP + manual overwrite pins
    """

    # HANDLE PIN MAP PARAMS (lp_name + custom pin lut)
    parsed_data = ["n/a"] if map_data is None else map_data.strip().split(';')
    if ':' in parsed_data[0]:
        lp_name = "n/a"
    else:
        lp_name = parsed_data.pop(0)
    # SAVE PARSED CUSTOM PIN OVERWRITE (manual mapping - MAPPING)
    try:
        PinMap.MAPPING = {pin.split(':')[0].strip(): int(pin.split(':')[1].strip()) for pin in parsed_data if ':' in pin}
    except Exception as e:
        # PARSE ERROR !!!
        print(f"[io] custom pin key(s) parse error: {e}")

    # SELECT LOOKUP TABLE BASED ON PLATFORM / User input
    if isinstance(lp_name, str) and lp_name != 'n/a':
        if f"LP_{lp_name}" in [lp.split('.')[0] for lp in dir() if lp.startswith('LP_')]:
            PinMap.MAPPING_LUT = lp_name
            return PinMap.MAPPING_LUT
    PinMap.MAPPING_LUT = detect_platform()
    return PinMap.MAPPING_LUT


def physical_pin(key):
    """
    Used in LoadModules
    key - resolve pin number by logical name (like: switch_1)
    This function implements protected IO allocation (overload protection)
     for protected LM functions (IO-booking)
    """
    # Get pin number on platform by pin key aka logical pin
    pin_num = __resolve_pin_number(key)
    if isinstance(pin_num, int):
        # Check pin is already used
        if pin_num in PinMap.IO_USE_DICT.keys():
            key_cache = PinMap.IO_USE_DICT[pin_num]
            if key_cache == key:
                print(f"[io] ReInit pin: {key_cache}:{pin_num}")
                return pin_num
            msg = f"[io] Pin {key} is busy: {key_cache}:{pin_num}"
            raise Exception(msg)
        # key: pin number, value: pin key (alias)
        PinMap.IO_USE_DICT[pin_num] = key
        print(f"[io] Init pin: {key}:{pin_num}")
    return pin_num


def get_pinmap():
    """
    Debug info function to get active pinmap and booked IO-s
    """
    return {'map': PinMap.MAPPING_LUT, 'booked': PinMap.IO_USE_DICT, 'custom': PinMap.MAPPING}


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
    :param key: logical pin name, example: neop, dht, etc.
    """
    custom_pin = PinMap.MAPPING.get(key, None)          # Get user custom pin map (if any)
    if custom_pin is None:
        # [1] Handle default pin resolve from static lut
        try:
            # LOAD LOOKUP TABLE
            exec(f'import LP_{PinMap.MAPPING_LUT}')
            # GET KEY PARAM VALUE
            out = eval(f'LP_{PinMap.MAPPING_LUT}.{key}')
            # Workaround to support normal python (tuple output), micropython (exact output - int)
            return int(out[0]) if isinstance(out, tuple) else out
        except Exception as e:
            # Missing LP module - don't die
            if "No module named" in str(e):
                return None
            # Other issue (key not found, etc...)
            raise Exception(f"[io-resolve] error: {e}")
    # [2] Handle user custom pins from cstmpmap (overwrite default)
    return custom_pin
