from time import time
# RGB (3x PWM) Channels
__FADER_OBJ = (None, None, None)
# COLOR_FROM (0-2), COLOR_TO (3-5), TIME_FROM_SEC(6), TIME_TO_SEC(7), COLOR_CURRENT (8-10), state: 0False 1True (11)
__FADER_CACHE = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
__PERSISTENT_CACHE = False


def __fader_init():
    global __FADER_OBJ
    if __FADER_OBJ[0] is None or __FADER_OBJ[1] is None or __FADER_OBJ[2] is None:
        from machine import Pin, PWM
        from LogicalPins import get_pin_on_platform_by_key
        red = Pin(get_pin_on_platform_by_key('pwm_1'))
        green = Pin(get_pin_on_platform_by_key('pwm_2'))
        blue = Pin(get_pin_on_platform_by_key('pwm_3'))
        __FADER_OBJ = (PWM(red, freq=1024),
                       PWM(green, freq=1024),
                       PWM(blue, freq=1024))
    return __FADER_OBJ


def __persistent_cache_manager(mode):
    """
    pds - persistent data structure
    modes:
        r - recover, s - save
    """
    if not __PERSISTENT_CACHE:
        return
    global __FADER_CACHE
    if mode == 's':
        # SAVE CACHE
        with open('fadergb.pds', 'w') as f:
            f.write(','.join([str(k) for k in __FADER_CACHE]))
        return
    try:
        # RESTORE CACHE
        with open('fadergb.pds', 'r') as f:
            __FADER_CACHE = [int(data) for data in f.read().strip().split(',')]
    except:
        pass


def __lerp(a, b, t):
    # Check ranges here
    t = 1 if t > 1 else t
    t = 0 if t < 0 else t
    out = (1 - t) * a + b * t
    return out


def __inv_lerp(a, b, v):
    if (b - a) == 0:
        return a
    return (v - a) / (b - a)


def fader_cache_load_n_init(cache=None):
    """
    Fader init: create owm objects and load cache
    """
    from sys import platform
    global __PERSISTENT_CACHE
    if cache is None:
        __PERSISTENT_CACHE = True if platform == 'esp32' else False
    else:
        __PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')  # recover data cache
    for ix, obj in enumerate(__fader_init()):
        obj.duty(__FADER_CACHE[ix+8])
    return "CACHE: {}".format(__PERSISTENT_CACHE)


def fade(r, g, b, sec=0):
    """
    Set RGB parameters to change under the given sec
    """
    global __FADER_CACHE
    if __FADER_CACHE[11] == 0:
        return "Fading is turned off, use Toggle to turn on"
    tim_now = time()
    # COLOR_FROM (0-2), COLOR_TO (3-5), TIME_FROM_SEC(6), TIME_TO_SEC(7), COLOR_CURRENT (8-10), state: 0False 1True (11)
    __FADER_CACHE[0:8] = __FADER_CACHE[8], __FADER_CACHE[9], __FADER_CACHE[10], r, g, b, tim_now, tim_now + sec
    transition()
    __persistent_cache_manager('s')
    return "Fading: {} -> {} -> {} ".format(__FADER_CACHE[0:3], __FADER_CACHE[8:11], __FADER_CACHE[3:6])


def transition():
    """
    Runs the transition: color change
    """
    global __FADER_CACHE
    ctime = time()
    if __FADER_CACHE[11] == 0 or __FADER_CACHE[8:11] == __FADER_CACHE[3:6]:
        return "Skipped (no change) / Manually turned off)"
    # COLOR_FROM (0-2), COLOR_TO (3-5), TIME_FROM_SEC(6), TIME_TO_SEC(7), COLOR_CURRENT (8-10), state: 0False 1True (11)
    state = __inv_lerp(__FADER_CACHE[6], __FADER_CACHE[7], ctime)
    for i, obj in enumerate(__fader_init()):
        # diff / color
        color = int(__lerp(__FADER_CACHE[i], __FADER_CACHE[i+3], state))
        if color == __FADER_CACHE[i+8]:
            continue
        # Set dimmer obj duty / channel
        obj.duty(color)
        # Store new from (actual) param / channel
        __FADER_CACHE[i+8] = color
    return "RGB: {} -> {} -> {} ".format(__FADER_CACHE[0:3], __FADER_CACHE[8:11], __FADER_CACHE[3:6])


def toggle(state=None):
    """
    Toggle led state based on the stored state or based on explicit input
    """
    # COLOR_FROM (0-2), COLOR_TO (3-5), TIME_FROM_SEC(6), TIME_TO_SEC(7), COLOR_CURRENT (8-10), state: 0False 1True (11)
    global __FADER_CACHE
    # Input handling
    nst = 1 if state else 0
    if state is None:
        # Toggle stored state
        nst = 0 if __FADER_CACHE[11] == 1 else 1
    # Set required state
    if nst == 0:
        for obj in __fader_init():
            obj.duty(0)
        __FADER_CACHE[11] = 0
        __persistent_cache_manager('s')
        return "RGB OFF"
    for ix, obj in enumerate(__fader_init()):
        obj.duty(__FADER_CACHE[ix+8])
    __FADER_CACHE[11] = 1
    __persistent_cache_manager('s')
    return "RGB ON"


#########################################
#                   HELP                #
#########################################


def help():
    return 'transition', 'fade r g b sec=0', 'toggle', 'fader_cache_load_n_init'
