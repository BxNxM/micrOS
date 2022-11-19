from sys import platform
from LogicalPins import physical_pin, pinmap_dump

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


def set_value(value=None):
    global __DIMMER_CACHE
    # restore data from cache if it was not provided
    value = int(__DIMMER_CACHE[1] if value is None else value)
    if 0 <= value <= 1000:
        __dimmer_init().duty(value)
        if value == 0:
            __DIMMER_CACHE[0] = 0        # SAVE STATE TO CACHE
        else:
            __DIMMER_CACHE[1] = value    # SAVE VALUE TO CACHE
            __DIMMER_CACHE[0] = 1        # SAVE STATE TO CACHE
        __persistent_cache_manager('s')
        return status()
    return "DIMMER ERROR, VALUE 0-1000 ONLY, GIVEN: {}".format(value)


def load_n_init(cache=None):
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


def toggle(state=None):
    """
    Toggle led state based on the stored one
    """
    if state is not None:
        __DIMMER_CACHE[0] = 0 if state else 1
    if __DIMMER_CACHE[0] == 1:
        return set_value(0)         # Set value to 0 - OFF
    return set_value()              # Set value to the cached - ON


def subscribe_presence(timer=30):
    """
    Initialize LM presence module with ON/OFF callback functions
    """
    from LM_presence import _subscribe
    _subscribe(on=lambda s=True: toggle(s), off=lambda s=False: toggle(s), timer=timer)


#######################
# LM helper functions #
#######################

def status(lmf=None):
    # Slider dedicated widget input - [OK]
    data = __DIMMER_CACHE
    return {'X': data[1], 'S': data[0]}


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins associated to the module
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_dump('dim_1')


def help():
    return 'set_value value=<0-1000>', 'toggle state=None', 'load_n_init',\
           'subscribe_presence', 'status', 'pinmap'
