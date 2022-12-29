from neopixel import NeoPixel
from machine import Pin
from sys import platform
from utime import sleep_ms
from Common import transition
from ConfigHandler import cfgget
from LogicalPins import physical_pin, pinmap_dump
from random import randint


#########################################
#       DIGITAL CONTROLLER PARAMS       #
#########################################
class Data:
    # Values: R, G, B, STATE_ON_OFF, IS_INITIALIZED
    DCACHE = [100, 100, 100, 0]
    CH_MAX = 255
    NEOPIXEL_OBJ = None
    PERSISTENT_CACHE = False
    FADE_OBJ = (None, None, None)


#########################################
#        DIGITAL rgb WITH 1 "PWM"       #
#########################################


def __init_NEOPIXEL(n=24):
    """
    Init NeoPixel module
    n - number of led fragments
    """
    if Data.NEOPIXEL_OBJ is None:
        neopixel_pin = Pin(physical_pin('neop'))     # Get Neopixel pin from LED PIN pool
        Data.NEOPIXEL_OBJ = NeoPixel(neopixel_pin, n)                 # initialize for max 8 segments
        del neopixel_pin
    return Data.NEOPIXEL_OBJ


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
        with open('neopixel.pds', 'w') as f:
            f.write(','.join([str(k) for k in Data.DCACHE]))
        return
    try:
        # RESTORE CACHE
        with open('neopixel.pds', 'r') as f:
            Data.DCACHE = [float(data) for data in f.read().strip().split(',')]
    except:
        pass


def load_n_init(cache=None, ledcnt=24):
    """
    Initiate NeoPixel RGB module
    :param cache bool: file state machine cache: True/False/None(default: automatic True)
    - Load .pds (state machine cache) for this load module
    - Apply loaded states to gpio pins (boot function)
    :return str: Cache state
    """
    if cache is None:
        Data.PERSISTENT_CACHE = False if platform == 'esp8266' else True
    else:
        Data.PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')         # recover data cache
    _ledcnt = __init_NEOPIXEL(n=ledcnt).n
    if Data.PERSISTENT_CACHE and Data.DCACHE[3] == 1:
        Data.DCACHE[3] = 0                  # Force ON at boot
        toggle(True)
    return "CACHE: {}, LED CNT: {}".format(Data.PERSISTENT_CACHE, _ledcnt)


def neopixel(r=None, g=None, b=None, smooth=True, force=True):
    """
    Set NEOPIXEL RGB values
    :param r: red value   0-254
    :param g: green value 0-254
    :param b: blue value  0-254
    :param smooth: runs colors change with smooth effect
    :param force: clean fade generators and set color
    :return dict: rgb status - states: R, G, B, S
    """

    def __buttery(r_from, g_from, b_from, r_to, g_to, b_to):
        step_ms = 2
        interval_sec = 0.3
        if Data.DCACHE[3] == 0:
            # Turn from OFF to on (to colors)
            r_from, g_from, b_from = 0, 0, 0
            Data.DCACHE[3] = 1
        r_gen = transition(from_val=r_from, to_val=r_to, step_ms=step_ms, interval_sec=interval_sec)
        g_gen = transition(from_val=g_from, to_val=g_to, step_ms=step_ms, interval_sec=interval_sec)
        b_gen = transition(from_val=b_from, to_val=b_to, step_ms=step_ms, interval_sec=interval_sec)
        for _r in r_gen:
            _g = g_gen.__next__()
            _b = b_gen.__next__()
            for lcnt in range(0, __init_NEOPIXEL().n):
                Data.NEOPIXEL_OBJ[lcnt] = (_r, _g, _b)
            Data.NEOPIXEL_OBJ.write()
            sleep_ms(1)

    r = Data.DCACHE[0] if r is None else r
    g = Data.DCACHE[1] if g is None else g
    b = Data.DCACHE[2] if b is None else b
    if force and Data.FADE_OBJ[0]:
        Data.FADE_OBJ = (None, None, None)
    # Set each LED for the same color
    if smooth:
        __buttery(r_from=Data.DCACHE[0], g_from=Data.DCACHE[1], b_from=Data.DCACHE[2], r_to=r, g_to=g, b_to=b)
    else:
        for element in range(0, __init_NEOPIXEL().n):          # Iterate over led string elements
            Data.NEOPIXEL_OBJ[element] = (r, g, b)             # Set LED element color
        Data.NEOPIXEL_OBJ.write()                              # Send data to device
    # Set cache
    if r > 0 or g > 0 or b > 0:
        Data.DCACHE = [r, g, b, 1]                         # Cache colors + state (True-ON)
    else:
        Data.DCACHE[3] = 0                                 # State - False - OFF
    __persistent_cache_manager('s')                        # Save cache - Data.DCACHE -  to file
    return status()


def brightness(percent=None, smooth=True):
    """
    Set neopixel brightness
    :param percent int: brightness percentage: 0-100
    :param smooth bool: enable smooth color transition: True(default)/False
    :return dict: rgb status - states: R, G, B, S
    """
    # Get color (channel) max brightness
    ch_max = max(Data.DCACHE[:-1])
    # Calculate actual brightness
    actual_percent = ch_max / Data.CH_MAX * 100

    # Return brightness percentage
    if percent is None:
        if Data.DCACHE[3] == 0:
            return "0 %"
        return "{} %".format(actual_percent)
    # Validate input percentage value
    if percent < 0 or percent > 100:
        return "Percent is out of range: 0-100"
    # Percent not changed
    if percent == actual_percent and Data.DCACHE[3] == 1:
        return status()

    # Set brightness percentage
    target_br = Data.CH_MAX * (percent / 100)
    new_rgb = (target_br * float(Data.DCACHE[0] / ch_max),
               target_br * float(Data.DCACHE[1] / ch_max),
               target_br * float(Data.DCACHE[2]) / ch_max)
    return neopixel(round(new_rgb[0], 3), round(new_rgb[1], 3), round(new_rgb[2], 3), smooth=smooth)


def segment(r=None, g=None, b=None, s=0, cache=False, write=True):
    """
    Set single segment by index on neopixel
    :param r: red value 0-254
    :param g: green value 0-254
    :param b: blue value 0-254
    :param s: segment - index 0-ledcnt
    :param cache: cache color (update .pds file)
    :param write: send color buffer to neopixel (update LEDs)
    :return dict: rgb status - states: R, G, B, S
    """
    r = Data.DCACHE[0] if r is None else r
    g = Data.DCACHE[1] if g is None else g
    b = Data.DCACHE[2] if b is None else b
    neo_n = __init_NEOPIXEL().n
    if s <= neo_n:
        Data.NEOPIXEL_OBJ[s] = (r, g, b)
        # Send colors to neopixel
        if write:
            Data.NEOPIXEL_OBJ.write()
        # Cache handling
        if cache:
            if r > 0 or g > 0 or b > 0:
                Data.DCACHE = [r, g, b, 1]
            else:
                Data.DCACHE[3] = 0
            __persistent_cache_manager('s')  # Save cache - Data.DCACHE -  to file

        return status()
    return "NEOPIXEL index error: {} > {}".format(s, neo_n)


def toggle(state=None, smooth=True):
    """
    Toggle led state based on the stored state
    :param state: True(1)/False(0)
    :param smooth: runs colors change with smooth effect
    :return dict: rgb status - states: R, G, B, S
    """
    # Set state directly (inverse) + check change
    if state is not None:
        if bool(state) is bool(Data.DCACHE[3]):
            return status()
        Data.DCACHE[3] = 0 if state else 1

    # Set OFF state (1)
    if Data.DCACHE[3] == 1:
        return neopixel(r=0, g=0, b=0, smooth=smooth, force=False)
    # Turn ON with smooth "hack" (0)
    if smooth:
        r, g, b = Data.DCACHE[0], Data.DCACHE[1], Data.DCACHE[2]
        Data.DCACHE[0], Data.DCACHE[1], Data.DCACHE[2] = 0, 0, 0
        return neopixel(r, g, b, smooth=smooth, force=False)
    # Turn ON without smooth (0)
    return neopixel(smooth=smooth, force=False)


def set_transition(r, g, b, sec):
    """
    Set transition color change for long dimming periods < 30sec
    - creates the color dimming generators
    :param r: red value   0-255
    :param g: green value 0-255
    :param b: blue value  0-255
    :param sec: transition length in sec
    :return: info msg string
    """
    Data.DCACHE[3] = 1
    timirqseq = cfgget('timirqseq')
    from_red = Data.DCACHE[0]
    from_green = Data.DCACHE[1]
    from_blue = Data.DCACHE[2]
    # Generate RGB color transition object (generator)
    Data.FADE_OBJ = (transition(from_val=from_red, to_val=r, step_ms=timirqseq, interval_sec=sec),
                     transition(from_val=from_green, to_val=g, step_ms=timirqseq, interval_sec=sec),
                     transition(from_val=from_blue, to_val=b, step_ms=timirqseq, interval_sec=sec))
    return 'Settings was applied... wait for: run_transition'


def run_transition():
    """
    Transition execution - color change for long dimming periods
    - runs the generated color dimming generators
    :return str: Execution verdict: Run / No Run
    """
    if None not in Data.FADE_OBJ:
        try:
            r = Data.FADE_OBJ[0].__next__()
            g = Data.FADE_OBJ[1].__next__()
            b = Data.FADE_OBJ[2].__next__()
            if Data.DCACHE[3] == 1:
                neopixel(int(r), int(g), int(b), smooth=False, force=False)
                return 'Run R{}R{}B{}'.format(r, g, b)
            return 'Run deactivated'
        except:
            Data.FADE_OBJ = (None, None, None)
            return 'GenEnd.'
    return 'Nothing to run.'


def random(smooth=True, max_val=254):
    """
    Demo function: implements random color change
    :param smooth bool: enable smooth color transition: True(default)/False
    :param max_val: set channel maximum generated value: 0-1000
    :return dict: rgb status - states: R, G, B, S
    """
    r = randint(0, max_val)
    g = randint(0, max_val)
    b = randint(0, max_val)
    return neopixel(r, g, b, smooth=smooth)


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
    # Neopixel(=RGB) dedicated widget input - [OK]
    data = Data.DCACHE
    return {'R': data[0], 'G': data[1], 'B': data[2], 'S': data[3]}


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_dump('neop')


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'neopixel r=<0-255> g b smooth=True force=True', 'toggle state=None smooth=True', \
           'load_n_init ledcnt=24', 'brightness percent=<0-100> smooth=True', 'segment r, g, b, s=<0-n>',\
           'set_transition r=<0-255> g b sec', 'run_transition',\
           'random smooth=True max_val=254', 'status', 'subscribe_presence', 'pinmap'
