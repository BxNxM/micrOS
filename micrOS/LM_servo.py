from machine import Pin, PWM
from LogicalPins import get_pin_on_platform_by_key

__SERVO = None
__SERVO2 = None

#########################################
#             SERVO CONTROL [1]         #
#########################################


def __SERVO_init():
    global __SERVO
    if __SERVO is None:
        try:
            pin = Pin(get_pin_on_platform_by_key('servo_1'))
            __SERVO = PWM(pin, freq=50)
            del pin
        except Exception as e:
            return str(e)
    return __SERVO


def sduty(duty=75):
    s = __SERVO_init()
    if duty > 115:
        duty = 115
    elif duty < 40:
        duty = 40
    try:
        # duty for sduty is between 40 - 115
        s.duty(duty)
        return "SET SERVO: duty: {}".format(duty)
    except Exception as e:
        return str(e)


def sdemo():
    from time import sleep
    sduty(40)
    sleep(1)
    sduty(115)
    sleep(1)
    sduty(75)
    return "sduty DEMO"

#########################################
#             SERVO CONTROL [2]         #
#########################################


def __SERVO2_init():
    global __SERVO2
    if __SERVO2 is None:
        try:
            pin = Pin(get_pin_on_platform_by_key('servo_2'))     # Alternative wiring
            __SERVO2 = PWM(pin, freq=50)
            del pin
        except Exception as e:
            return str(e)
    return __SERVO2


def s2duty(duty=75):
    s = __SERVO2_init()
    if duty > 115:
        duty = 115
    elif duty < 40:
        duty = 40
    try:
        # duty for sduty is between 40 - 115
        s.duty(duty)
        return "SET SERVO: duty: {}".format(duty)
    except Exception as e:
        return str(e)


#########################################
#                 HELP                  #
#########################################

def help():
    return 'sduty(duty=<int>40-115)', 'sdemo', 's2duty'
