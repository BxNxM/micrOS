from sys import platform
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
    TRAN_OBJS = (None, None, None)


#########################################
#        DIGITAL rgb WITH 1 "PWM"       #
#########################################


def __init_NEOPIXEL(n=24):
    """
    Init NeoPixel module
    n - number of led fragments
    n - must be set from code! (no persistent object handling in LMs)
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
    if cache is None:
        Data.PERSISTENT_CACHE = False if platform == 'esp8266' else True
    else:
        Data.PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')        # recover data cache
    _ledcnt = __init_NEOPIXEL(n=ledcnt).n
    if Data.PERSISTENT_CACHE and Data.DCACHE[3] == 1:
        neopixel()                         # Set each LED for the same color
    return "CACHE: {}, LED CNT: {}".format(Data.PERSISTENT_CACHE, _ledcnt)


def neopixel(r=None, g=None, b=None):
    """
    Simple NeoPixel wrapper
    - Set all led fragments for the same color set
    - Default and cached color scheme
    """
    r = Data.DCACHE[0] if r is None else r
    g = Data.DCACHE[1] if g is None else g
    b = Data.DCACHE[2] if b is None else b
    # Set each LED for the same color
    for element in range(0, __init_NEOPIXEL().n):    # Iterate over led string elements
        Data.NEOPIXEL_OBJ[element] = (r, g, b)             # Set LED element color
    Data.NEOPIXEL_OBJ.write()                              # Send data to device
    # Set cache
    if r > 0 or g > 0 or b > 0:
        Data.DCACHE = [r, g, b, 1]                         # Cache colors + state (True-ON)
    else:
        Data.DCACHE[3] = 0                                 # State - False - OFF
    __persistent_cache_manager('s')                # Save cache - Data.DCACHE -  to file
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


def toggle(state=None):
    """
    ON - OFF NeoPixel
    """
    if state is not None:
        Data.DCACHE[3] = 0 if state else 1
    if Data.DCACHE[3] == 1:
        neopixel(r=0, g=0, b=0)
        return "OFF"
    neopixel(Data.DCACHE[0], Data.DCACHE[1], Data.DCACHE[2])
    return "ON"


def set_transition(r, g, b, sec):
    timirqseq = cfgget('timirqseq')
    from_red = Data.DCACHE[0]
    from_green = Data.DCACHE[1]
    from_blue = Data.DCACHE[2]
    # Generate RGB color transition object (generator)
    Data.TRAN_OBJS = (transition(from_val=from_red, to_val=r, step_ms=timirqseq, interval_sec=sec),
                   transition(from_val=from_green, to_val=g, step_ms=timirqseq, interval_sec=sec),
                   transition(from_val=from_blue, to_val=b, step_ms=timirqseq, interval_sec=sec))
    return 'Settings was applied.'


def run_transition():
    if None not in Data.TRAN_OBJS:
        try:
            r = Data.TRAN_OBJS[0].__next__()
            g = Data.TRAN_OBJS[1].__next__()
            b = Data.TRAN_OBJS[2].__next__()
            neopixel(int(r), int(g), int(b))
            return 'Run R{}R{}B{}'.format(r, g, b)
        except:
            Data.TRAN_OBJS = (None, None, None)
            return 'GenEnd.'
    return 'Nothing to run.'


#######################
# LM helper functions #
#######################

def help():
    return 'neopixel r=<0-255> g b n=<0-24)', 'toggle state=None', \
           'load_n_init ledcnt=24', 'segment r, g, b, s=<0-n>',\
           'set_transition r=<0-255> g b sec', 'run_transition'
