from machine import Pin
from LogicalPins import get_pin_on_platform_by_key

#########################################
#           DIGITAL IO SWITCH           #
#########################################
__SWITCH_OBJ = [None, None, None, None]
__PERSISTENT_CACHE = False
__SWITCH_STATE = [0, 0, 0, 0]


#########################################
#          COMMON CACHE HANDLING        #
#########################################

def __persistent_cache_manager(mode):
    """
    pds - persistent data structure
    modes:
        r - recover, s - save
    """
    if not __PERSISTENT_CACHE:
        return
    global __SWITCH_STATE
    if mode == 's':
        # SAVE CACHE
        with open('switch.pds', 'w') as f:
            f.write(','.join([str(k) for k in __SWITCH_STATE]))
        return
    try:
        # RESTORE CACHE
        with open('switch.pds', 'r') as f:
            __SWITCH_STATE = [int(data) for data in f.read().strip().split(',')]
    except:
        pass


def __init_switches_state(state=None, ch_init=None):
    if ch_init is None:
        ch_init = []
    # Init selected channels
    if 1 in ch_init:
        set_state(state)
    if 2 in ch_init:
        set_state2(state)
    if 3 in ch_init:
        set_state3(state)
    if 4 in ch_init:
        set_state4(state)


def switch_cache_load_n_init(cache=None, ch_init=None):
    if ch_init is None:
        ch_init = []
    from sys import platform
    global __PERSISTENT_CACHE
    if cache is None:
        __PERSISTENT_CACHE = True if platform == 'esp32' else False
    else:
        __PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')
    if __PERSISTENT_CACHE and __SWITCH_STATE[0] == 1:
        # Set up channels from cache
        __init_switches_state(ch_init=ch_init)
    else:
        # Set up selected channels to 0
        __init_switches_state(state=0, ch_init=ch_init)
    return "CACHE: {}".format(__PERSISTENT_CACHE)

#########################################
#      SWITCH1 DIGITAL 0,1 OUTPUT       #
#########################################


def __switch_init():
    if __SWITCH_OBJ[0] is None:
        __SWITCH_OBJ[0] = Pin(get_pin_on_platform_by_key('switch_1'), Pin.OUT)
    return __SWITCH_OBJ[0]


def set_state(state=None):
    state = __SWITCH_STATE[0] if state is None else int(state)
    if state in (0, 1):
        __switch_init().value(state)
        __SWITCH_STATE[0] = state
        __persistent_cache_manager('s')
    else:
        return "[ERROR] switch input have to 0 or 1"
    return "SET STATE: {}".format(state)


def toggle():
    """
    Toggle led state based on the stored one
    """
    new_state = 1 if __SWITCH_STATE[0] == 0 else 0
    return set_state(new_state)


#########################################
#      SWITCH2 DIGITAL 0,1 OUTPUT       #
#########################################


def __switch2_init():
    if __SWITCH_OBJ[1] is None:
        __SWITCH_OBJ[1] = Pin(get_pin_on_platform_by_key('switch_2'), Pin.OUT)
    return __SWITCH_OBJ[1]


def set_state2(state=None):
    state = __SWITCH_STATE[1] if state is None else int(state)
    if state in (0, 1):
        __switch2_init().value(state)
        __SWITCH_STATE[1] = state
        __persistent_cache_manager('s')
    else:
        return "[ERROR] switch input have to 0 or 1"
    return "SET STATE(2): {}".format(state)


def toggle2():
    """
    Toggle led state based on the stored one
    """
    new_state = 1 if __SWITCH_STATE[1] == 0 else 0
    return set_state2(new_state)

#########################################
#      SWITCH3 DIGITAL 0,1 OUTPUT       #
#########################################


def __switch3_init():
    if __SWITCH_OBJ[2] is None:
        __SWITCH_OBJ[2] = Pin(get_pin_on_platform_by_key('switch_3'), Pin.OUT)
    return __SWITCH_OBJ[2]


def set_state3(state=None):
    state = __SWITCH_STATE[2] if state is None else int(state)
    if state in (0, 1):
        __switch3_init().value(state)
        __SWITCH_STATE[2] = state
        __persistent_cache_manager('s')
    else:
        return "[ERROR] switch input have to 0 or 1"
    return "SET STATE(3): {}".format(state)


def toggle3():
    """
    Toggle led state based on the stored one
    """
    new_state = 1 if __SWITCH_STATE[2] == 0 else 0
    return set_state3(new_state)

#########################################
#      SWITCH3 DIGITAL 0,1 OUTPUT       #
#########################################


def __switch4_init():
    if __SWITCH_OBJ[3] is None:
        __SWITCH_OBJ[3] = Pin(get_pin_on_platform_by_key('switch_4'), Pin.OUT)
    return __SWITCH_OBJ[3]


def set_state4(state=None):
    state = __SWITCH_STATE[3] if state is None else int(state)
    if state in (0, 1):
        __switch4_init().value(state)
        __SWITCH_STATE[3] = state
        __persistent_cache_manager('s')
    else:
        return "[ERROR] switch input have to 0 or 1"
    return "SET STATE(4): {}".format(state)


def toggle4():
    """
    Toggle led state based on the stored one
    """
    new_state = 1 if __SWITCH_STATE[3] == 0 else 0
    return set_state4(new_state)


#########################################
#                   HELP                #
#########################################

def help():
    return 'set_state state=<0,1>', 'toggle', \
           'switch_cache_load_n_init cache=None<True/False> ch_init=[1,2,3,4]', \
           'set_state2 state=<0,1>', 'toggle2', \
           'set_state3 state=<0,1>', 'toggle3', \
           'set_state4 state=<0,1>', 'toggle4', \
           '[!]PersistentStateCacheDisabledOn:esp8266'
