from machine import Pin, PWM
from LogicalPins import physical_pin, pinmap_dump


class Data:
    S_OBJ = None
    S_OBJ2 = None
    S = 75
    S2 = 75

#########################################
#             S_OBJ CONTROL [1]         #
#########################################


def __servo_init():
    if Data.S_OBJ is None:
        try:
            pin = Pin(physical_pin('servo_1'))
            Data.S_OBJ = PWM(pin, freq=50)
            del pin
        except Exception as e:
            return str(e)
    return Data.S_OBJ


def sduty(duty=75):
    """
    Set servo (1) position
    :param duty: servo duty position 40-115, default: 75
    :return: verdict
    """
    s = __servo_init()
    if duty > 115:
        duty = 115
    elif duty < 40:
        duty = 40
    try:
        # duty for sduty is between 40 - 115
        s.duty(duty)
        Data.S = duty
        return "SET SERVO1: duty: {}".format(duty)
    except Exception as e:
        return str(e)


def sdemo():
    """
    Demo move function for sduty (1)
    """
    from utime import sleep
    sduty(40)
    sleep(1)
    sduty(115)
    sleep(1)
    sduty(75)
    return "sduty DEMO"

#########################################
#             S_OBJ CONTROL [2]         #
#########################################


def __servo2_init():
    if Data.S_OBJ2 is None:
        try:
            pin = Pin(physical_pin('servo_2'))     # Alternative wiring
            Data.S_OBJ2 = PWM(pin, freq=50)
            del pin
        except Exception as e:
            return str(e)
    return Data.S_OBJ2


def s2duty(duty=75):
    """
    Set servo (2) position
    :param duty: servo duty position 40-115, default: 75
    :return: verdict
    """
    s = __servo2_init()
    if duty > 115:
        duty = 115
    elif duty < 40:
        duty = 40
    try:
        # duty for sduty is between 40 - 115
        s.duty(duty)
        Data.S2 = duty
        return "SET SERVO2: duty: {}".format(duty)
    except Exception as e:
        return str(e)


def deinit():
    """
    Deinit servo motors
    - stop pwm channels (sduty/s2duty)
    """
    if Data.S_OBJ:
        Data.S_OBJ.deinit()
        Data.S_OBJ = None
    if Data.S_OBJ2:
        Data.S_OBJ2.deinit()
        Data.S_OBJ2 = None
    return 'Deinit servo 1 and 2'


#######################
# LM helper functions #
#######################

def status(lmf=None):
    """
    [i] micrOS LM naming convention
    Show Load Module state machine
    :param lmf str: selected load module function aka (function to show state of): None (show all states)
    - lmf: sduty, s2duty
    - micrOS client state synchronization
    :return dict: S1(X), S2(X)
    """
    # Slider dedicated widget input - [OK]
    if lmf is None:
        return {'S1': Data.S, 'S2': Data.S2}
    elif lmf.strip() == 's2duty':
        return {'X': Data.S2}
    else:
        return {'X': Data.S}


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_dump(['servo_1', 'servo_2'])


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'sduty duty=<int>40-115', 'sdemo', 's2duty', 'deinit', 'status', 'pinmap'
