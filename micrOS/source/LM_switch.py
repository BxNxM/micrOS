from machine import Pin
from LogicalPins import physical_pin, pinmap_dump

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


def load_n_init(cache=None, ch_init=None):
    """
    Initiate switch module (4 switch pack)
    :param cache bool: file state machine cache: True/False/None(default: automatic True)
    - Load .pds (state machine cache) for this load module
    - Apply loaded states to gpio pins (boot function)
    :return str: Cache state
    """
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
        __SWITCH_OBJ[0] = Pin(physical_pin('switch_1'), Pin.OUT)
    return __SWITCH_OBJ[0]


def set_state(state=None):
    """
    Set switch (1) state
    :param state bool: True/False/None(default: use cached value)
    :return: verdict
    """
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
    Toggle switch (1) state based on current state
    :return: set_state verdict
    """
    new_state = 1 if __SWITCH_STATE[0] == 0 else 0
    return set_state(new_state)


#########################################
#      SWITCH2 DIGITAL 0,1 OUTPUT       #
#########################################


def __switch2_init():
    if __SWITCH_OBJ[1] is None:
        __SWITCH_OBJ[1] = Pin(physical_pin('switch_2'), Pin.OUT)
    return __SWITCH_OBJ[1]


def set_state2(state=None):
    """
    Set switch (2) state
    :param state bool: True/False/None(default: use cached value)
    :return: verdict
    """
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
    Toggle switch (2) state based on current state
    :return: set_state verdict
    """
    new_state = 1 if __SWITCH_STATE[1] == 0 else 0
    return set_state2(new_state)

#########################################
#      SWITCH3 DIGITAL 0,1 OUTPUT       #
#########################################


def __switch3_init():
    if __SWITCH_OBJ[2] is None:
        __SWITCH_OBJ[2] = Pin(physical_pin('switch_3'), Pin.OUT)
    return __SWITCH_OBJ[2]


def set_state3(state=None):
    """
    Set switch (3) state
    :param state bool: True/False/None(default: use cached value)
    :return: verdict
    """
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
    Toggle switch (3) state based on current state
    :return: set_state verdict
    """
    new_state = 1 if __SWITCH_STATE[2] == 0 else 0
    return set_state3(new_state)

#########################################
#      SWITCH3 DIGITAL 0,1 OUTPUT       #
#########################################


def __switch4_init():
    if __SWITCH_OBJ[3] is None:
        __SWITCH_OBJ[3] = Pin(physical_pin('switch_4'), Pin.OUT)
    return __SWITCH_OBJ[3]


def set_state4(state=None):
    """
    Set switch (4) state
    :param state bool: True/False/None(default: use cached value)
    :return: verdict
    """
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
    Toggle switch (4) state based on current state
    :return: set_state verdict
    """
    new_state = 1 if __SWITCH_STATE[3] == 0 else 0
    return set_state4(new_state)


#######################
# LM helper functions #
#######################

def status(lmf=None):
    """
    [i] micrOS LM naming convention
    Show Load Module state machine
    :param lmf str: selected load module function aka (function to show state of): None (show all states)
    - lmf: set_stateX, toggleX - X: 1,2,3,4
    - micrOS client state synchronization
    :return dict: SW1, SW2, SW3, SW4 -> S
    """
    if lmf is None:
        return {'SW1': __SWITCH_STATE[0], 'SW2': __SWITCH_STATE[1],
                'SW3': __SWITCH_STATE[2], 'SW4': __SWITCH_STATE[3]}
    if lmf[-1].isdigit():
        id = int(lmf[-1])
        if id == 2:
            return {'S': __SWITCH_STATE[1]}
        if id == 3:
            return {'S': __SWITCH_STATE[2]}
        if id == 4:
            return {'S': __SWITCH_STATE[3]}
    return {'S': __SWITCH_STATE[0]}


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_dump(['switch_1', 'switch_2', 'switch_3', 'switch_4'])


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'set_state state=<0,1>', 'toggle', \
           'set_state2 state=<0,1>', 'toggle2', \
           'set_state3 state=<0,1>', 'toggle3', \
           'set_state4 state=<0,1>', 'toggle4', \
           'load_n_init cache=None<True/False> ch_init=[1,2,3,4]',\
           'status'
