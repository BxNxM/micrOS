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

# LOAD PIN MAP MODULE: USER/AUTOMATIC(DEFAULT)
if 'esp32' in platform:
    from LP_esp32 import *
elif 'esp8266' in platform:
    from LP_esp8266 import *


# GET MODULE VARIABLE: SELECTED LOGICAL PIN ON BOARD
def get_pin_on_platform_by_key(key):
    try:
        return eval(key)
    except Exception:
        return None
