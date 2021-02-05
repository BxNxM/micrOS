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
        from LogicalPins import get_pin_on_platform_by_key
        dimmer_pin = Pin(get_pin_on_platform_by_key('pwm_5'))
        __DIMMER_OBJ = PWM(dimmer_pin, freq=480)
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
        return "SET DIMMER: {}".format(value)
    return "DIMMER ERROR, VALUE 0-1000 ONLY, GIVEN: {}".format(value)


def dimmer_cache_load_n_init(cache=None):
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

#########################################
#                   HELP                #
#########################################


def help():
    return 'set_value(value=<0-1000>)', 'toggle(state=None)',\
           'dimmer_cache_load_n_init(cache=True)', \
           '[!]PersistentStateCacheDisabledOn:esp8266'
