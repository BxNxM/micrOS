#########################################
#       ANALOG rgb CONTROLLER PARAMS    #
#########################################
from sys import platform
from Common import transition
from ConfigHandler import cfgget


class Data:
    RGB_OBJS = (None, None, None)
    RGB_CACHE = [197, 35, 10, 0]           # R, G, B (default color) + RGB state (default: off)
    PERSISTENT_CACHE = False
    FADE_OBJS = (None, None, None)


#########################################
#      ANALOG rgb WITH 3 channel PWM    #
#########################################

def __RGB_init():
    if Data.RGB_OBJS[0] is None or Data.RGB_OBJS[1] is None or Data.RGB_OBJS[2] is None:
        from machine import Pin, PWM
        from LogicalPins import physical_pin
        red = Pin(physical_pin('redgb'))
        green = Pin(physical_pin('rgreenb'))
        blue = Pin(physical_pin('rgbue'))
        if platform == 'esp8266':
            Data.RGB_OBJS = (PWM(red, freq=1024),
                          PWM(green, freq=1024),
                          PWM(blue, freq=1024))
        else:
            Data.RGB_OBJS = (PWM(red, freq=20480),
                          PWM(green, freq=20480),
                          PWM(blue, freq=20480))
    return Data.RGB_OBJS


def __persistent_cache_manager(mode):
    """
    pds - persistent data structure
    modes:
        r - recover, s - save
    """
    if not Data.PERSISTENT_CACHE:
        return
    if mode == 's':
        # SAVE CACHE
        with open('rgb.pds', 'w') as f:
            f.write(','.join([str(k) for k in Data.RGB_CACHE]))
        return
    try:
        # RESTORE CACHE
        with open('rgb.pds', 'r') as f:
            Data.RGB_CACHE = [int(data) for data in f.read().strip().split(',')]
    except:
        pass


def load_n_init(cache=None):
    from sys import platform
    if cache is None:
        Data.PERSISTENT_CACHE = True if platform == 'esp32' else False
    else:
        Data.PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')      # recover data cache if enabled
    if Data.RGB_CACHE[3] == 1:
        rgb()
    else:
        rgb(0, 0, 0)                     # If no persistent cache, init all pins low (OFF)
    return "CACHE: {}".format(Data.PERSISTENT_CACHE)


def rgb(r=None, g=None, b=None):
    __RGB_init()
    # Dynamic input handling: user/cache
    r = Data.RGB_CACHE[0] if r is None else r
    g = Data.RGB_CACHE[1] if g is None else g
    b = Data.RGB_CACHE[2] if b is None else b
    # Set RGB channels
    Data.RGB_OBJS[0].duty(r)
    Data.RGB_OBJS[1].duty(g)
    Data.RGB_OBJS[2].duty(b)
    # Save channel duties if LED on
    if r > 0 or g > 0 or b > 0:
        Data.RGB_CACHE = [Data.RGB_OBJS[0].duty(), Data.RGB_OBJS[1].duty(), Data.RGB_OBJS[2].duty(), 1]
    else:
        Data.RGB_CACHE[3] = 0
    # Save config
    __persistent_cache_manager('s')
    return "SET rgb: R{}G{}B{}".format(r, g, b)


def toggle(state=None):
    """
    Toggle led state based on the stored one
    """
    if state is not None:
        Data.RGB_CACHE[3] = 0 if state else 1
    if Data.RGB_CACHE[3]:
        rgb(0, 0, 0)
        return "OFF"
    rgb()
    return "ON"


def set_transition(r, g, b, sec):
    Data.RGB_CACHE[3] = 1
    timirqseq = cfgget('timirqseq')
    from_red = Data.RGB_CACHE[0]
    from_green = Data.RGB_CACHE[1]
    from_blue = Data.RGB_CACHE[2]
    # Generate RGB color transition object (generator)
    Data.FADE_OBJS = (transition(from_val=from_red, to_val=r, step_ms=timirqseq, interval_sec=sec),
                      transition(from_val=from_green, to_val=g, step_ms=timirqseq, interval_sec=sec),
                      transition(from_val=from_blue, to_val=b, step_ms=timirqseq, interval_sec=sec))
    return 'Settings was applied.'


def run_transition():
    if None not in Data.FADE_OBJS:
        try:
            r = Data.FADE_OBJS[0].__next__()
            g = Data.FADE_OBJS[1].__next__()
            b = Data.FADE_OBJS[2].__next__()
            if Data.RGB_CACHE[3] == 1:
                rgb(int(r), int(g), int(b))
                return 'Run R{}R{}B{}'.format(r, g, b)
            return 'Run deactivated'
        except:
            Data.FADE_OBJS = (None, None, None)
            return 'GenEnd.'
    return 'Nothing to run.'


#######################
# LM helper functions #
#######################

def help():
    return 'rgb r=<0-1000> g=<0-1000> b=<0,1000>',\
           'toggle state=None', 'load_n_init', \
           'set_transition r=<0-255> g b sec', 'run_transition'
