from machine import Pin, PWM
from LogicalPins import physical_pin, pinmap_dump

#########################################
#     ANALOG DIMMER CONTROLLER PARAMS   #
#########################################
__L298N_OBJS = []
# DATA: SPEED (PWM obj), dir pin1, dir pin2


#########################################
#         ANALOG DIMMER WITH PWM        #
#########################################

def __l298n_init():
    global __L298N_OBJS
    if len(__L298N_OBJS) == 0:
        __L298N_OBJS.append(PWM(Pin(physical_pin('l298speed')), freq=50))
        __L298N_OBJS.append(Pin(physical_pin('l298dir_1'), Pin.OUT))
        __L298N_OBJS.append(Pin(physical_pin('l298dir_2'), Pin.OUT))
        __L298N_OBJS[0].duty(0)     # Set default speed (PWM)
        __L298N_OBJS[1].value(0)    # Set default direction for dc motor1
        __L298N_OBJS[2].value(1)    # Set default direction for dc motor1
    return __L298N_OBJS


def m1_control(direc=None, speed=None):
    out = {}
    if direc is not None:
        out = set_direction(direc)
    if speed is not None:
        out.update(set_speed(speed))
    return out


def set_speed(speed=100):
    if 0 <= speed <= 1000:
        print(__l298n_init())
        __l298n_init()[0].duty(speed)
        return {'speed': speed}
    return {'speed': 'value range error'}


def stop():
    return set_speed(0)


def set_direction(direc=0):
    """
    direc (direction) values:
    0: forward
    1: backward
    """
    objlist = __l298n_init()
    if direc == 0:
        objlist[1].value(1)
        objlist[2].value(0)
        return {'direction': 'forward'}
    objlist[1].value(0)
    objlist[2].value(1)
    return {'direction': 'backward'}


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
    return pinmap_dump(['l298speed', 'l298dir_1', 'l298dir_2'])


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'm1_control direc=<0/1> speed=<0-1023>', 'set_speed <0-1023>',\
           'set_direction <0-1>', 'stop', 'pinmap'
