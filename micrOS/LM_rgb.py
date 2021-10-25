#########################################
#       ANALOG rgb CONTROLLER PARAMS    #
#########################################
from sys import platform
from Common import transition
from ConfigHandler import cfgget
from utime import sleep_ms


class Data:
    """
    Runtime static state machine class
    """
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
    """
    Initiate RGB module
    - Load .pds file for that module
    - restore state machine from .pds
    :param cache: file state machine chache: True(default)/False
    :return: Cache state
    """
    from sys import platform
    if cache is None:
        Data.PERSISTENT_CACHE = True if platform == 'esp32' else False
    else:
        Data.PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')      # recover data cache if enabled
    if Data.RGB_CACHE[3] == 1:
        toggle(True)
    else:
        rgb(0, 0, 0, smooth=False)       # If no persistent cache, init all pins low (OFF)
    return "CACHE: {}".format(Data.PERSISTENT_CACHE)


def rgb(r=None, g=None, b=None, smooth=True):
    """
    Set RGB values with PWM signal
    :param r: red value   0-1000
    :param g: green value 0-1000
    :param b: blue value  0-1000
    :param smooth: runs colors change with smooth effect
    :return: verdict string
    """
    def __buttery(r_from, g_from, b_from, r_to, g_to, b_to):
        step_ms = 2
        interval_sec = 0.3
        r_gen = transition(from_val=r_from, to_val=r_to, step_ms=step_ms, interval_sec=interval_sec)
        g_gen = transition(from_val=g_from, to_val=g_to, step_ms=step_ms, interval_sec=interval_sec)
        b_gen = transition(from_val=b_from, to_val=b_to, step_ms=step_ms, interval_sec=interval_sec)
        for _r in r_gen:
            Data.RGB_OBJS[0].duty(_r)
            Data.RGB_OBJS[1].duty(g_gen.__next__())
            Data.RGB_OBJS[2].duty(b_gen.__next__())
            sleep_ms(step_ms)

    __RGB_init()
    # Dynamic input handling: user/cache
    r = Data.RGB_CACHE[0] if r is None else r
    g = Data.RGB_CACHE[1] if g is None else g
    b = Data.RGB_CACHE[2] if b is None else b
    # Set RGB channels
    if smooth:
        __buttery(r_from=Data.RGB_CACHE[0], g_from=Data.RGB_CACHE[1], b_from=Data.RGB_CACHE[2], r_to=r, g_to=g, b_to=b)
    else:
        Data.RGB_OBJS[0].duty(r)
        Data.RGB_OBJS[1].duty(g)
        Data.RGB_OBJS[2].duty(b)
    # Save channel duties if LED on
    if r > 0 or g > 0 or b > 0:
        Data.RGB_CACHE = [Data.RGB_OBJS[0].duty(), Data.RGB_OBJS[1].duty(), Data.RGB_OBJS[2].duty(), 1]
    else:
        Data.RGB_CACHE[3] = 0
    # Save state machine (cache)
    __persistent_cache_manager('s')
    return "SET rgb: R{}G{}B{}".format(r, g, b)


def toggle(state=None, smooth=True):
    """
    Toggle led state based on the stored state
    :param state: True(1)/False(0)
    :param smooth: runs colors change with smooth effect
    :return: verdict
    """
    # State auto invert
    if state is not None:
        Data.RGB_CACHE[3] = 0 if state else 1
    # Set OFF state
    if Data.RGB_CACHE[3]:
        rgb(0, 0, 0, smooth=smooth)
        return "OFF"
    # Turn ON with smooth "hack"
    if smooth:
        r, g, b = Data.RGB_CACHE[0], Data.RGB_CACHE[1], Data.RGB_CACHE[2]
        Data.RGB_CACHE[0], Data.RGB_CACHE[1], Data.RGB_CACHE[2] = 0, 0, 0
        rgb(r, g, b)
        return "ON"
    # Turn ON without smooth
    rgb()
    return "ON"


def set_transition(r, g, b, sec):
    """
    Set transition color change for long dimming periods < 30sec
    - creates the color dimming generators
    :param r: red value   0-1000
    :param g: green value 0-1000
    :param b: blue value  0-1000
    :param sec: transition length in sec
    :return: info msg string
    """
    # Set by cron OR manual "effect"
    Data.RGB_CACHE[3] = 1
    timirqseq = cfgget('timirqseq')
    from_red = Data.RGB_CACHE[0]
    from_green = Data.RGB_CACHE[1]
    from_blue = Data.RGB_CACHE[2]
    # Generate RGB color transition object (generator)
    Data.FADE_OBJS = (transition(from_val=from_red, to_val=r, step_ms=timirqseq, interval_sec=sec),
                      transition(from_val=from_green, to_val=g, step_ms=timirqseq, interval_sec=sec),
                      transition(from_val=from_blue, to_val=b, step_ms=timirqseq, interval_sec=sec))
    return 'Settings was applied... wait for: run_transition'


def run_transition():
    """
    Transition execution - color change for long dimming periods
    - runs the generated color dimming generators
    :return: Execution verdict
    """
    if None not in Data.FADE_OBJS:
        try:
            r = Data.FADE_OBJS[0].__next__()
            g = Data.FADE_OBJS[1].__next__()
            b = Data.FADE_OBJS[2].__next__()
            # Check output enabled - LED is ON
            if Data.RGB_CACHE[3] == 1:
                rgb(int(r), int(g), int(b), smooth=False)
                return 'Transition R{}R{}B{}'.format(r, g, b)
            return 'Transition deactivated'
        except:
            Data.FADE_OBJS = (None, None, None)
            return 'Transition done'
    return 'Nothing to run.'


#######################
# LM helper functions #
#######################

def help():
    return 'rgb r=<0-1000> g=<0-1000> b=<0,1000> smooth=True',\
           'toggle state=None smooth=True', 'load_n_init', \
           'set_transition r=<0-1000> g b sec', 'run_transition'
