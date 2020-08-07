#########################################
#           DIGITAL IO SWITCH           #
#########################################
__SWITCH_OBJ = None
__PERSISTENT_CACHE = True

#########################################
#      ANALOG RGB WITH 3 channel PWM    #
#########################################


def __SWITCH_init():
    global __SWITCH_OBJ
    if __SWITCH_OBJ is None:
        from machine import Pin
        from LogicalPins import get_pin_on_platform_by_key
        __SWITCH_OBJ = Pin(get_pin_on_platform_by_key('switch'), Pin.OUT)
        switch_cache_load_n_init('r')
    return __SWITCH_OBJ


def switch_cache_load_n_init(mode='r', datain=0, cache=None):
    global __PERSISTENT_CACHE
    if cache is not None:
        __PERSISTENT_CACHE = cache
    """
    pds - persistent data structure
    modes:
        r - recover
        s - save
    """
    if not __PERSISTENT_CACHE:
        return
    if mode == 's':
        # SAVE CACHE
        try:
            with open('switch.pds', 'w') as f:
                f.write("{}".format(datain))
                return
        except Exception:
            return
    try:
        # RESTORE CACHE
        with open('switch.pds', 'r') as f:
            __SWITCH_init().value(int(f.read().strip()))
    except Exception:
        pass


def set_state(state):
    if state in (0, 1):
        __SWITCH_init().value(state)
        switch_cache_load_n_init('s', state)
    else:
        return "[ERROR] switch input have to 0 or 1"
    return "SET STATE: {}".format(state)


def toggle():
    """
    Toggle led state based on the stored one
    """
    switch_obj = __SWITCH_init()
    new_state = 1 if switch_obj.value() == 0 else 0
    switch_obj.value(new_state)
    switch_cache_load_n_init('s', new_state)
    return "SET STATE: {}".format(new_state)


#########################################
#                   HELP                #
#########################################

def help():
    return 'set_state(state=<0,1>)', 'toggle', 'switch_cache_load_n_init'
