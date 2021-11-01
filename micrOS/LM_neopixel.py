from sys import platform
from utime import sleep_ms
from Common import transition
from ConfigHandler import cfgget


#########################################
#       DIGITAL CONTROLLER PARAMS       #
#########################################
class Data:
    # Values: R, G, B, STATE_ON_OFF, IS_INITIALIZED
    DCACHE = [100, 100, 100, 0]
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
        from neopixel import NeoPixel
        from machine import Pin
        from LogicalPins import physical_pin
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
            Data.DCACHE = [int(data) for data in f.read().strip().split(',')]
    except:
        pass


def load_n_init(cache=None, ledcnt=24):
    """
    Initiate NeoPixel RGB module
    - Load .pds file for that module
    - restore state machine from .pds
    :param cache: file state machine chache: True(default)/False
    :param ledcnt: led segment count (for addressing) - should be set in boothook
    :return: Cache state
    """
    if cache is None:
        Data.PERSISTENT_CACHE = False if platform == 'esp8266' else True
    else:
        Data.PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')        # recover data cache
    _ledcnt = __init_NEOPIXEL(n=ledcnt).n
    if Data.PERSISTENT_CACHE and Data.DCACHE[3] == 1:
        toggle(True)
    return "CACHE: {}, LED CNT: {}".format(Data.PERSISTENT_CACHE, _ledcnt)


def neopixel(r=None, g=None, b=None, smooth=True, force=True):
    """
    Set NEOPIXEL RGB values
    :param r: red value   0-255
    :param g: green value 0-255
    :param b: blue value  0-255
    :param smooth: runs colors change with smooth effect
    :param force: clean fade generators and set color
    :return: verdict string
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
    return "NEOPIXEL SET TO R{}G{}B{}".format(r, g, b)


def segment(r=None, g=None, b=None, s=0, cache=False, write=True):
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

        return "NEOPIXEL[{}] R{}G{}B{}".format(s, r, g, b)
    return "NEOPIXEL index error: {} > {}".format(s, neo_n)


def toggle(state=None, smooth=True):
    """
    Toggle led state based on the stored state
    :param state: True(1)/False(0)
    :param smooth: runs colors change with smooth effect
    :return: verdict
    """
    if state is not None:
        Data.DCACHE[3] = 0 if state else 1
    if Data.DCACHE[3] == 1:
        neopixel(r=0, g=0, b=0, smooth=smooth, force=False)
        return "OFF"
    # Turn ON with smooth "hack"
    if smooth:
        r, g, b = Data.DCACHE[0], Data.DCACHE[1], Data.DCACHE[2]
        Data.DCACHE[0], Data.DCACHE[1], Data.DCACHE[2] = 0, 0, 0
        neopixel(r, g, b, force=False)
        return "ON"
    # Turn ON without smooth
    neopixel(force=False)
    return "ON"


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
    Transition execution/"stepping"
    - run color change for long dimming periods
        - runs the generated color dimming generators
    :return: Execution verdict
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


#######################
# LM helper functions #
#######################

def status(lmf=None):
    # Neopixel(=RGB) dedicated widget input - [OK]
    return {'R': Data.DCACHE[0], 'G': Data.DCACHE[1], 'B': Data.DCACHE[2], 'S': Data.DCACHE[3]}


def help():
    return 'neopixel r=<0-255> g b smooth=True force=True', 'toggle state=None smooth=True', \
           'load_n_init ledcnt=24', 'segment r, g, b, s=<0-n>',\
           'set_transition r=<0-255> g b sec', 'run_transition', 'status'
