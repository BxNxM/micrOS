from sys import platform
from LogicalPins import physical_pin, pinmap_dump
from Common import transition
from utime import sleep_ms

#########################################
#     ANALOG DIMMER CONTROLLER PARAMS   #
#########################################
__DIMMER_OBJ = None
# DATA: state:ON/OFF, value:0-1000
__DIMMER_CACHE = [0, 500]
__PERSISTENT_CACHE = False


#########################################
#         ANALOG DIMMER WITH PWM        #
#########################################

def __dimmer_init():
    global __DIMMER_OBJ
    if __DIMMER_OBJ is None:
        from machine import Pin, PWM
        dimmer_pin = Pin(physical_pin('dim_1'))
        if platform == 'esp8266':
            __DIMMER_OBJ = PWM(dimmer_pin, freq=1024)
        else:
            __DIMMER_OBJ = PWM(dimmer_pin, freq=20480)
    return __DIMMER_OBJ


def __persistent_cache_manager(mode='r'):
    """
    pds - persistent data structure
    modes:
        r - recover, s - save
    """
    if not __PERSISTENT_CACHE:
        return
    global __DIMMER_CACHE
    if mode == 's':
        # SAVE CACHE
        with open('dimmer.pds', 'w') as f:
            f.write(','.join([str(k) for k in __DIMMER_CACHE]))
        return
    try:
        # RESTORE CACHE
        with open('dimmer.pds', 'r') as f:
            __DIMMER_CACHE = [int(data) for data in f.read().strip().split(',')]
    except:
        pass


#########################
# Application functions #
#########################

def load_n_init(cache=None):
    """
    Initiate dimmer module
    :param cache bool: file state machine cache: True/False/None(default: automatic True)
    - Load .pds (state machine cache) for this load module
    - Apply loaded states to gpio pins (boot function)
    :return str: Cache state
    """
    from sys import platform
    global __PERSISTENT_CACHE
    if cache is None:
        __PERSISTENT_CACHE = False if platform == 'esp8266' else True
    else:
        __PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')
    if __PERSISTENT_CACHE and __DIMMER_CACHE[0] == 1:
        set_value()
    else:
        set_value(0)
    return "CACHE: {}".format(__PERSISTENT_CACHE)


def set_value(value=None, smooth=True):
    """
    Set dimmer values with PWM signal
    :param value int: value 0-1000 default: None (set cached value)
    :param smooth bool: run channel change with smooth effect
    :return dict: X, S
    """
    global __DIMMER_CACHE

    def __buttery(c_from, c_to):
        step_ms = 2
        interval_sec = 0.2
        if __DIMMER_CACHE[0] == 0:
            # Turn from OFF to on (to whites)
            c_from = 0
        gen = transition(from_val=c_from, to_val=c_to, step_ms=step_ms, interval_sec=interval_sec)
        for _t in gen:
            __dimmer_init().duty(_t)
            sleep_ms(step_ms)

    # restore data from cache if it was not provided
    value = int(__DIMMER_CACHE[1] if value is None else value)
    if 0 <= value <= 1000:
        if smooth:
            __buttery(__DIMMER_CACHE[1], value)
        else:
            # Set value
            __dimmer_init().duty(value)
        # State handling
        if value == 0:
            __DIMMER_CACHE[0] = 0        # SAVE STATE TO CACHE
        else:
            __DIMMER_CACHE[1] = value    # SAVE VALUE TO CACHE
            __DIMMER_CACHE[0] = 1        # SAVE STATE TO CACHE
        __persistent_cache_manager('s')
        return status()
    return "DIMMER ERROR, VALUE 0-1000 ONLY, GIVEN: {}".format(value)


def toggle(state=None, smooth=True):
    """
    Toggle dimmer state based on the stored state
    :param state bool: True(1)/False(0)/None(default - automatic toggle)
    :param smooth bool: run channel change with smooth effect
    :return dict: X, S
    """
    if state is not None:
        __DIMMER_CACHE[0] = 0 if state else 1
    if __DIMMER_CACHE[0] == 1:
        return set_value(0, smooth=smooth)         # Set value to 0 - OFF
    return set_value(smooth=smooth)                # Set value to the cached - ON


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
    :return dict: X, S
    """
    # Slider dedicated widget input - [OK]
    data = __DIMMER_CACHE
    return {'X': data[1], 'S': data[0]}


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_dump('dim_1')


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'set_value value=<0-1000> smooth=True', 'toggle state=None smooth=True', 'load_n_init',\
           'subscribe_presence', 'status', 'pinmap'
