#########################################
#       DIGITAL CONTROLLER PARAMS       #
#########################################
# Values: R, G, B, STATE_ON_OFF, IS_INITIALIZED
__DCACHE = [100, 100, 100, 0]
__NEOPIXEL_OBJ = None
__PERSISTENT_CACHE = True

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


def __persistent_cache_manager(mode='r'):
    global __DCACHE
    """
    pds - persistent data structure
    modes:
        r - recover
        s - save
    """
    if not __PERSISTENT_CACHE:
        return
    if mode == 's':
        # SAVE CACHE
        try:
            with open('neopixel.pds', 'w') as f:
                f.write("{},{},{},{}".format(__DCACHE[0], __DCACHE[1], __DCACHE[2], __DCACHE[3]))
                return
        except:
            return
    try:
        # RESTORE CACHE
        with open('neopixel.pds', 'r') as f:
            __DCACHE = [int(data) for data in f.read().strip().split(',')]
    except Exception:
        pass


def neopixel_cache_load_n_init(n=8, cache=True):
    global __PERSISTENT_CACHE
    __PERSISTENT_CACHE = cache
    __persistent_cache_manager(mode='r')                # recover data cache
    if cache and __DCACHE[3] == 1:
        # Set each LED for the same color
        __init_NEOPIXEL(n=n)
        for element in range(0, __init_NEOPIXEL().n):   # Iterate over led string elements
            __NEOPIXEL_OBJ[element] = (__DCACHE[0], __DCACHE[1], __DCACHE[2])  # Set LED element color
        __NEOPIXEL_OBJ.write()                          # Send data to device
    return "CACHE: {}".format(cache)


def neopixel(r=None, g=None, b=None, n=8):
    """
    Simple NeoPixel wrapper
    - Set all led fragments for the same color set
    - Default and cached color scheme
    """
    global __DCACHE
    r = __DCACHE[0] if r is None else r
    g = __DCACHE[1] if g is None else g
    b = __DCACHE[2] if b is None else b
    # Set each LED for the same color
    for element in range(0, __init_NEOPIXEL(n=n).n):   # Iterate over led string elements
        __NEOPIXEL_OBJ[element] = (r, g, b)         # Set LED element color
    __NEOPIXEL_OBJ.write()                          # Send data to device
    # Set cache
    if r > 0 or g > 0 or b > 0:
        __DCACHE = [r, g, b, 1]                     # Cache colors + state (True-ON)
    else:
        __DCACHE[3] = 0                             # State - False - OFF
    __persistent_cache_manager(mode='s')            # Save cache - __DCACHE -  to file
    return "NEOPIXEL WAS SET R{}G{}B{}".format(r, g, b)


def neopixel_segment(s=0, r=None, g=None, b=None):
    r = __DCACHE[0] if r is None else r
    g = __DCACHE[1] if g is None else g
    b = __DCACHE[2] if b is None else b
    if s <= __init_NEOPIXEL().n:
        __NEOPIXEL_OBJ[s] = (r, g, b)
        __NEOPIXEL_OBJ.write()
        return "NEOPIXEL {} SEGMENT WAS SET R{}G{}B{}".format(s, r, g, b)
    return "NEOPIXEL s={} SEGMENT OVERLOAD".format(s)


def neopixel_toggle():
    """
    ON - OFF NeoPixel
    """
    global __DCACHE
    if __DCACHE[3] == 1:
        neopixel(r=0, g=0, b=0)                     # 0,0,0 sets status OFF - not saved to cache
    else:
        neopixel(__DCACHE[0], __DCACHE[1], __DCACHE[2])
        __DCACHE[3] = 1
    return "ON" if __DCACHE[3] == 1 else "OFF"

#########################################
#                   HELP                #
#########################################


def help():
    return 'neopixel(r=<0-255>, g, b, n=8', 'neopixel_toggle', \
           'neopixel_cache_load_n_init(n=<led_count>, cache=True', \
           'neopixel_segment(s=<0-n>, r, g, b'
