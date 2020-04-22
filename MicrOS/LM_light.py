#########################################
#       ANALOG RGB CONTROLLER PARAMS    #
#########################################
__RLED = None
__GLED = None
__BLED = None

#########################################
# ANALOG !OR! DIGITAL CONTROLLER PARAMS #
#########################################
__RGB_STATE = False
__RGB_CACHE = (800, 800, 800)

#########################################
#           DIGITAL PARAMS              #
#########################################
__NEOPIXEL_OBJ = None


#########################################
#      ANALOG RGB WITH 3 channel PWM    #
#########################################

def __RGB_init():
    global __RLED, __GLED, __BLED
    if __RLED is None or __GLED is None or __BLED is None:
        from machine import Pin, PWM
        from LogicalPins import get_pin_on_platform_by_key
        d7_gpio13_red = Pin(get_pin_on_platform_by_key('pwm_1'))
        d4_gpio2_green = Pin(get_pin_on_platform_by_key('pwm_2'))
        d3_gpio0_blue = Pin(get_pin_on_platform_by_key('pwm_3'))
        __RLED = PWM(d7_gpio13_red, freq=80)
        __GLED = PWM(d4_gpio2_green, freq=80)
        __BLED = PWM(d3_gpio0_blue, freq=80)


def RGB(r=None, g=None, b=None):
    global __RGB_STATE
    __RGB_init()
    _rgb_state = False
    if r is not None:
        __RLED.duty(r)
        _rgb_state = _rgb_state or (True if r > 0 else False)
    if g is not None:
        __GLED.duty(g)
        _rgb_state = _rgb_state or (True if g > 0 else False)
    if b is not None:
        __BLED.duty(b)
        _rgb_state = _rgb_state or (True if b > 0 else False)
    __RGB_STATE = _rgb_state
    return "SET RGB"


def RGB_deinit():
    global __RGB_STATE
    RGB(0,0,0)
    __RGB_STATE = False
    return "DEINIT RGB"


def RGB_toggle():
    """
    Toggle led state based on the stored one
    """
    global __RGB_STATE, __RGB_CACHE
    if __RGB_STATE:
        __RGB_STATE = False
        __RGB_CACHE = __RLED.duty(), __GLED.duty(), __BLED.duty()
        RGB(0, 0, 0)
    else:
        __RGB_STATE = True
        RGB(__RGB_CACHE[0], __RGB_CACHE[1], __RGB_CACHE[2])
    return "ON" if __RGB_STATE else "OFF"

#########################################
#        DIGITAL RGB WITH 1 "PWM"       #
#########################################

def __init_NEOPIXEL():
    """
    Init NeoPixel module
    """
    global __NEOPIXEL_OBJ
    if __NEOPIXEL_OBJ is None:
        from neopixel import NeoPixel
        from machine import Pin
        from LogicalPins import get_pin_on_platform_by_key
        neopixel_pin = Pin(get_pin_on_platform_by_key('pwm_3'))  # Get Neopixel pin from LED PIN pool
        __NEOPIXEL_OBJ = NeoPixel(neopixel_pin, 8)           # initialize for max 8 segments
    return __NEOPIXEL_OBJ


def neopixel(r=None, g=None, b=None):
    """
    Simple NeoPixel wrapper
    - Set all led fragments for the same color set
    - Default and cached color scheme
    - TODO: Set elements by index support
    """
    global __RGB_CACHE
    r = __RGB_CACHE[0] if r is None else r
    g = __RGB_CACHE[1] if g is None else g
    b = __RGB_CACHE[2] if b is None else b
    for element in range(0, __init_NEOPIXEL().n):   # Iterate over led string elements
        __NEOPIXEL_OBJ[element] = (r, g, b)         # Set LED element color
    __NEOPIXEL_OBJ.write()                          # Send data to device
    if r > 0 or g > 0 or b > 0:
        __RGB_CACHE = (r, g, b)                     # Cache colors
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
    return 'RGB', 'RGB_toggle', 'neopixel', 'neopixel_toggle', 'RGB_deinit'
