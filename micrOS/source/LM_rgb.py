#########################################
#       ANALOG rgb CONTROLLER PARAMS    #
#########################################
from machine import Pin, PWM
from sys import platform
from Common import transition
from ConfigHandler import cfgget
from utime import sleep_ms
from LogicalPins import physical_pin, pinmap_dump
from random import randint


class Data:
    """
    Runtime static state machine class
    """
    RGB_OBJS = (None, None, None)
    RGB_CACHE = [197, 35, 10, 0]           # R, G, B (default color) + RGB state (default: off)
    PERSISTENT_CACHE = False
    FADE_OBJS = (None, None, None)
    CH_MAX = 1000                          # maximum value per channel


#########################################
#      ANALOG rgb WITH 3 channel PWM    #
#########################################

def __RGB_init():
    if Data.RGB_OBJS[0] is None or Data.RGB_OBJS[1] is None or Data.RGB_OBJS[2] is None:
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
            Data.RGB_CACHE = [float(data) for data in f.read().strip().split(',')]
    except:
        pass


def load_n_init(cache=None):
    """
    Initiate RGB module
    :param cache bool: file state machine cache: True/False/None(default: automatic True)
    - Load .pds (state machine cache) for this load module
    - Apply loaded states to gpio pins (boot function)
    :return str: Cache state
    """
    from sys import platform
    if cache is None:
        Data.PERSISTENT_CACHE = True if platform == 'esp32' else False
    else:
        Data.PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')     # recover data cache if enabled
    if Data.RGB_CACHE[3] == 1:
        Data.RGB_CACHE[3] = 0           # Force ON at boot
        toggle(True)
    else:
        rgb(0, 0, 0, smooth=False)      # If no persistent cache, init all pins low (OFF)
    return "CACHE: {}".format(Data.PERSISTENT_CACHE)


def rgb(r=None, g=None, b=None, smooth=True, force=True):
    """
    Set RGB values with PWM signal
    :param r int: red value   0-1000
    :param g int: green value 0-1000
    :param b int: blue value  0-1000
    :param smooth bool: enable smooth color transition: True(default)/False
    :param force bool: clean fade generators and set color (default: True)
    :return dict: rgb status - states: R, G, B, S
    """
    def __buttery(r_from, g_from, b_from, r_to, g_to, b_to):
        step_ms = 2
        interval_sec = 0.3
        if Data.RGB_CACHE[3] == 0:
            # Turn from OFF to on (to colors)
            r_from, g_from, b_from = 0, 0, 0
            Data.RGB_CACHE[3] = 1
        r_gen = transition(from_val=r_from, to_val=r_to, step_ms=step_ms, interval_sec=interval_sec)
        g_gen = transition(from_val=g_from, to_val=g_to, step_ms=step_ms, interval_sec=interval_sec)
        b_gen = transition(from_val=b_from, to_val=b_to, step_ms=step_ms, interval_sec=interval_sec)
        for _r in r_gen:
            Data.RGB_OBJS[0].duty(_r)
            Data.RGB_OBJS[1].duty(g_gen.__next__())
            Data.RGB_OBJS[2].duty(b_gen.__next__())
            sleep_ms(step_ms)

    __RGB_init()
    if force and Data.FADE_OBJS[0]:
        Data.FADE_OBJS = (None, None, None)
    # Dynamic input handling: user/cache
    r = Data.RGB_CACHE[0] if r is None else r
    g = Data.RGB_CACHE[1] if g is None else g
    b = Data.RGB_CACHE[2] if b is None else b
    # Set RGB channels
    if smooth:
        __buttery(r_from=Data.RGB_CACHE[0], g_from=Data.RGB_CACHE[1], b_from=Data.RGB_CACHE[2], r_to=r, g_to=g, b_to=b)
    else:
        Data.RGB_OBJS[0].duty(int(r))
        Data.RGB_OBJS[1].duty(int(g))
        Data.RGB_OBJS[2].duty(int(b))
    # Save channel duties if LED on
    if r > 0 or g > 0 or b > 0:
        Data.RGB_CACHE = [r, g, b, 1]
    else:
        Data.RGB_CACHE[3] = 0
    # Save state machine (cache)
    __persistent_cache_manager('s')
    return status()


def brightness(percent=None, smooth=True):
    """
    Set RGB brightness
    :param percent int: brightness percentage: 0-100
    :param smooth bool: enable smooth color transition: True(default)/False
    :return dict: rgb status - states: R, G, B, S
    """
    # Get color (channel) max brightness
    ch_max = max(Data.RGB_CACHE[:-1])
    # Calculate actual brightness
    actual_percent = ch_max / Data.CH_MAX * 100

    # Return brightness percentage
    if percent is None:
        if Data.RGB_CACHE[3] == 0:
            return "0 %"
        return "{} %".format(actual_percent)
    # Validate input percentage value
    if percent < 0 or percent > 100:
        return "Percent is out of range: 0-100"
    # Percent not changed
    if percent == actual_percent and Data.RGB_CACHE[3] == 1:
        return status()

    # Set brightness percentage
    target_br = Data.CH_MAX * (percent / 100)
    new_rgb = (target_br * float(Data.RGB_CACHE[0] / ch_max),
               target_br * float(Data.RGB_CACHE[1] / ch_max),
               target_br * float(Data.RGB_CACHE[2]) / ch_max)
    return rgb(round(new_rgb[0], 3), round(new_rgb[1], 3), round(new_rgb[2], 3), smooth=smooth)


def toggle(state=None, smooth=True):
    """
    Toggle led state based on the stored state
    :param state bool: True(1)/False(0)/None(default - automatic toggle)
    :param smooth bool: enable smooth color transition: True(default)/False
    :return dict: rgb status - states: R, G, B, S
    """
    # Set state directly (inverse) + check change
    if state is not None:
        if bool(state) is bool(Data.RGB_CACHE[3]):
            return status()
        Data.RGB_CACHE[3] = 0 if state else 1

    # Set OFF state (1)
    if Data.RGB_CACHE[3]:
        return rgb(0, 0, 0, smooth=smooth, force=False)
    # Turn ON with smooth "hack" (0)
    if smooth:
        r, g, b = Data.RGB_CACHE[0], Data.RGB_CACHE[1], Data.RGB_CACHE[2]
        Data.RGB_CACHE[0], Data.RGB_CACHE[1], Data.RGB_CACHE[2] = 0, 0, 0
        return rgb(r, g, b, smooth=smooth, force=False)
    # Turn ON without smooth (0)
    return rgb(smooth=smooth, force=False)


def set_transition(r, g, b, sec):
    """
    Set transition color change for long dimming periods < 30sec
    - creates the color dimming generators
    :param r int: red value   0-1000
    :param g int: green value 0-1000
    :param b int: blue value  0-1000
    :param sec int: transition length in sec
    :return str: info msg string
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
    :return str: Execution verdict: Run / No Run
    """
    if None not in Data.FADE_OBJS:
        try:
            r = Data.FADE_OBJS[0].__next__()
            g = Data.FADE_OBJS[1].__next__()
            b = Data.FADE_OBJS[2].__next__()
            # Check output enabled - LED is ON
            if Data.RGB_CACHE[3] == 1:
                rgb(int(r), int(g), int(b), smooth=False, force=False)
                return 'Transition R{}R{}B{}'.format(r, g, b)
            return 'Transition deactivated'
        except:
            Data.FADE_OBJS = (None, None, None)
            return 'Transition done'
    return 'Nothing to run.'


def random(smooth=True, max_val=1000):
    """
    Demo function: implements random color change
    :param smooth bool: enable smooth color transition: True(default)/False
    :param max_val: set channel maximum generated value: 0-1000
    :return dict: rgb status - states: R, G, B, S
    """
    r = randint(0, max_val)
    g = randint(0, max_val)
    b = randint(0, max_val)
    return rgb(r, g, b, smooth=smooth)


def subscribe_presence():
    """
    Initialize LM presence module with ON/OFF callback functions
    :return: None
    """
    from LM_presence import _subscribe
    _subscribe(on=lambda s=True: toggle(s), off=lambda s=False: toggle(s))

#######################
# LM helper functions #
#######################


def status(lmf=None):
    """
    [i] micrOS LM naming convention
    Show Load Module state machine
    :param lmf str: selected load module function aka (function to show state of): None (show all states)
    - micrOS client state synchronization
    :return dict: R, G, B, S
    """
    data = Data.RGB_CACHE
    return {'R': data[0], 'G': data[1], 'B': data[2], 'S': data[3]}


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_dump(['redgb', 'rgreenb', 'rgbue'])


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'rgb r=<0-1000> g=<0-1000> b=<0,1000> smooth=True force=True',\
           'toggle state=None smooth=True', 'load_n_init', \
           'brightness percent=<0-100> smooth=True',\
           'set_transition r=<0-1000> g b sec', 'run_transition',\
           'random smooth=True max_val=1000', 'status', 'subscribe_presence', 'pinmap'
