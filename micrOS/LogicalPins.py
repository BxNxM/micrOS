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
__ACTIVE_PIN_MAPPING = None


# GET MODULE VARIABLE: SELECTED LOGICAL PIN ON BOARD
def get_pin_on_platform_by_key(key, lpsname=None):
    global __ACTIVE_PIN_MAPPING
    # SELECT LOOKUP TABLE BASED ON PLATFORM
    if __ACTIVE_PIN_MAPPING is None or isinstance(lpsname, str):
        __ACTIVE_PIN_MAPPING = platform if lpsname is None else lpsname
    try:
        # LOAD LOOKUP TABLE
        exec('import LP_{}'.format(__ACTIVE_PIN_MAPPING))
        # GET KEY PARAM VALUE
        return eval('LP_{}.{}'.format(__ACTIVE_PIN_MAPPING, key))
    except Exception:
        return None
