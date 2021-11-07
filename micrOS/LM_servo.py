from machine import Pin, PWM
from LogicalPins import physical_pin


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
    # Slider dedicated widget input - [OK]
    if lmf is None:
        return {'S1': Data.S, 'S2': Data.S2}
    elif lmf.strip() == 's2duty':
        return {'X': Data.S2}
    else:
        return {'X': Data.S}


def pinmap():
    # Return module used PIN mapping
    return {'servo_1': physical_pin('servo_1'), 'servo_2': physical_pin('servo_2')}


def help():
    return 'sduty duty=<int>40-115', 'sdemo', 's2duty', 'deinit', 'status', 'pinmap'
