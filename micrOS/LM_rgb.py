#########################################
#       ANALOG rgb CONTROLLER PARAMS    #
#########################################
__RGB_OBJS = (None, None, None)
__RGB_CACHE = [600, 600, 600, 0]           # R, G, B, RGB state
__PERSISTENT_CACHE = False


#########################################
#      ANALOG rgb WITH 3 channel PWM    #
#########################################

def __RGB_init():
    global __RGB_OBJS
    if __RGB_OBJS[0] is None or __RGB_OBJS[1] is None or __RGB_OBJS[2] is None:
        from machine import Pin, PWM
        from LogicalPins import get_pin_on_platform_by_key
        red = Pin(get_pin_on_platform_by_key('redgb'))
        green = Pin(get_pin_on_platform_by_key('rgreenb'))
        blue = Pin(get_pin_on_platform_by_key('rgbue'))
        __RGB_OBJS = (PWM(red, freq=1024),
                      PWM(green, freq=1024),
                      PWM(blue, freq=1024))
    return __RGB_OBJS


def __persistent_cache_manager(mode):
    """
    pds - persistent data structure
    modes:
        r - recover, s - save
    """
    if not __PERSISTENT_CACHE:
        return
    global __RGB_CACHE
    if mode == 's':
        # SAVE CACHE
        with open('rgb.pds', 'w') as f:
            f.write(','.join([str(k) for k in __RGB_CACHE]))
        return
    try:
        # RESTORE CACHE
        with open('rgb.pds', 'r') as f:
            __RGB_CACHE = [int(data) for data in f.read().strip().split(',')]
    except:
        pass


def rgb_cache_load_n_init(cache=None):
    from sys import platform
    global __PERSISTENT_CACHE
    if cache is None:
        __PERSISTENT_CACHE = True if platform == 'esp32' else False
    else:
        __PERSISTENT_CACHE = cache
    rgb(0, 0, 0)                           # Init pins at bootup
    __persistent_cache_manager('r')        # recover data cache
    if __PERSISTENT_CACHE and __RGB_CACHE[3] == 1:
        rgb()                              # Recover state if ON
    return "CACHE: {}".format(__PERSISTENT_CACHE)


def rgb(r=None, g=None, b=None):
    global __RGB_CACHE
    r = __RGB_CACHE[0] if r is None else r
    g = __RGB_CACHE[1] if g is None else g
    b = __RGB_CACHE[2] if b is None else b
    __RGB_init()
    __RGB_CACHE[3] = False
    __RGB_OBJS[0].duty(r)
    __RGB_CACHE[3] |= True if r > 0 else False
    __RGB_OBJS[1].duty(g)
    __RGB_CACHE[3] |= True if g > 0 else False
    __RGB_OBJS[2].duty(b)
    __RGB_CACHE[3] |= True if b > 0 else False
    # Cache channel duties if ON
    if __RGB_CACHE[3]:
        __RGB_CACHE = [__RGB_OBJS[0].duty(), __RGB_OBJS[1].duty(), __RGB_OBJS[2].duty(), 1]
    else:
        __RGB_CACHE[3] = 0
    # Save config
    __persistent_cache_manager('s')
    return "SET rgb: R{}G{}B{}".format(r, g, b)


def toggle(state=None):
    """
    Toggle led state based on the stored one
    """
    if state is not None:
        __RGB_CACHE[3] = 0 if state else 1
    if __RGB_CACHE[3]:
        rgb(0, 0, 0)
        return "OFF"
    rgb()
    return "ON"


#########################################
#                   HELP                #
#########################################

def help():
    return 'rgb(r=<0-1000>, g=<0-1000>, b=<0,1000>)',\
           'toggle(state=None)', \
           'rgb_cache_load_n_init(cache=None<True/False>)',\
           '[!]PersistentStateCacheDisabledOn:esp8266'
