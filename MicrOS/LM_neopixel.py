#########################################
#       DIGITAL CONTROLLER PARAMS       #
#########################################
__RGB_STATE = False
__RGB_CACHE = (150, 150, 150)
__NEOPIXEL_OBJ = None

#########################################
#        DIGITAL RGB WITH 1 "PWM"       #
#########################################

def __init_NEOPIXEL(n=8):
    """
    Init NeoPixel module
    n - number of led fragments
    """
    global __NEOPIXEL_OBJ
    if __NEOPIXEL_OBJ is None:
        from neopixel import NeoPixel
        from machine import Pin
        from LogicalPins import get_pin_on_platform_by_key
        neopixel_pin = Pin(get_pin_on_platform_by_key('pwm_3'))     # Get Neopixel pin from LED PIN pool
        __NEOPIXEL_OBJ = NeoPixel(neopixel_pin, n)                  # initialize for max 8 segments
    return __NEOPIXEL_OBJ


def neopixel(r=None, g=None, b=None, n=8):
    """
    Simple NeoPixel wrapper
    - Set all led fragments for the same color set
    - Default and cached color scheme
    - TODO: Set elements by index support
    """
    global __RGB_CACHE, __RGB_STATE
    r = __RGB_CACHE[0] if r is None else r
    g = __RGB_CACHE[1] if g is None else g
    b = __RGB_CACHE[2] if b is None else b
    for element in range(0, __init_NEOPIXEL(n=n).n):   # Iterate over led string elements
        __NEOPIXEL_OBJ[element] = (r, g, b)         # Set LED element color
    __NEOPIXEL_OBJ.write()                          # Send data to device
    if r > 0 or g > 0 or b > 0:
        __RGB_CACHE = (r, g, b)                     # Cache colors
        __RGB_STATE = True
    else:
        __RGB_STATE = False
    return "NEOPIXEL WAS SET R{}G{}B{}".format(r, g, b)


def neopixel_toggle():
    """
    ON - OFF NeoPixel
    """
    global __RGB_STATE
    if __RGB_STATE:
        neopixel(r=0, g=0, b=0)
        __RGB_STATE = False
    else:
        neopixel(__RGB_CACHE[0], __RGB_CACHE[1], __RGB_CACHE[2])
        __RGB_STATE = True
    return "ON" if __RGB_STATE else "OFF"

#########################################
#                   HELP                #
#########################################

def help():
    return 'neopixel', 'neopixel_toggle'
