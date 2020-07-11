#########################################
#           DIGITAL IO SWITCH           #
#########################################
__SWITCH_OBJ = None

#########################################
#      ANALOG RGB WITH 3 channel PWM    #
#########################################


def __SWITCH_init():
    global __SWITCH_OBJ
    if __SWITCH_OBJ is None:
        from machine import Pin
        from LogicalPins import get_pin_on_platform_by_key
        __SWITCH_OBJ = Pin(get_pin_on_platform_by_key('switch'), Pin.OUT)
    return __SWITCH_OBJ


def set_state(state):
    if state in (0, 1):
        __SWITCH_init().value(state)
    else:
        return "[ERROR] switch input have to 0 or 1"
    return "SET STATE: {}".format(state)


def toggle():
    """
    Toggle led state based on the stored one
    """
    switch_obj = __SWITCH_init()
    switch_obj.value(1 if switch_obj.value() == 0 else 0)
    return switch_obj.value()


#########################################
#                   HELP                #
#########################################

def help():
    return 'set_state(state=<0,1>)', 'toggle'
