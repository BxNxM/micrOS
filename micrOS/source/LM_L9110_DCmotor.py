from LogicalPins import physical_pin, pinmap_dump

#########################################
#     ANALOG DIMMER CONTROLLER PARAMS   #
#########################################
__L9110_OBJS = []
# DATA: SPEED (PWM obj), dir pin1, dir pin2


#########################################
#         ANALOG DIMMER WITH PWM        #
#########################################

def __l9110_init():
    global __L9110_OBJS
    if len(__L9110_OBJS) == 0:
        from machine import Pin, PWM
        __L9110_OBJS.append(PWM(Pin(physical_pin('l9110dir_1')), freq=1024))
        __L9110_OBJS.append(PWM(Pin(physical_pin('l9110dir_2')), freq=1024))
        __L9110_OBJS[0].duty(0)     # Set default speed (PWM)
        __L9110_OBJS[1].duty(0)     # Set default speed (PWM)
    return __L9110_OBJS


def motor_control(direc=None, speed=None):
    if 0 > speed > 1000 or direc not in (0, 1):
        return 'invalid parameters'
    pwm_list = __l9110_init()
    if direc == 0:
        pwm_list[1].duty(0)
        pwm_list[0].duty(speed)
        return {'speed': speed, 'direc': 'forward'}
    pwm_list[0].duty(0)
    pwm_list[1].duty(speed)
    return {'speed': speed, 'direc': 'backward'}


#######################
# LM helper functions #
#######################
def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_dump(['l9110dir_1', 'l9110dir_2'])


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'motor_control direc=<0/1> speed=<0-1000>', 'pinmap'
