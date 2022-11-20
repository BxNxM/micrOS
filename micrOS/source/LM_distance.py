from machine import Pin, time_pulse_us
from utime import sleep_us
from LogicalPins import physical_pin, pinmap_dump

__TRIGGER_OBJ = None
__ECHO_OBJ = None


def __init_HCSR04():
    global __TRIGGER_OBJ, __ECHO_OBJ
    if __TRIGGER_OBJ is None or __ECHO_OBJ is None:
        trigger_pin = physical_pin('hcsrtrig')
        echo_pin = physical_pin('hcsrecho')
        # Init trigger pin (out)
        __TRIGGER_OBJ = Pin(trigger_pin, mode=Pin.OUT, pull=None)
        __TRIGGER_OBJ.value(0)
        # Init echo pin (in)
        __ECHO_OBJ = Pin(echo_pin, mode=Pin.IN, pull=None)
    return __TRIGGER_OBJ, __ECHO_OBJ


def __send_pulse_and_wait(echo_timeout_us=1000000):
    trigger_pin, echo_pin = __init_HCSR04()
    trigger_pin.value(0) # Stabilize the sensor
    sleep_us(5)
    trigger_pin.value(1)
    # Send a 10us pulse.
    sleep_us(10)
    trigger_pin.value(0)
    try:
        pulse_time = time_pulse_us(echo_pin, 1, echo_timeout_us)
        return pulse_time
    except OSError as ex:
        if ex.args[0] == 110: # 110 = ETIMEDOUT
            raise OSError('Out of range')
        raise ex


#########################
# Application functions #
#########################

def distance_mm():
    """
    To calculate the distance we get the pulse_time and divide it by 2
    (the pulse walk the distance twice) and by 29.1 becasue
    the sound speed on air (343.2 m/s), that It's equivalent to
    0.34320 mm/us that is 1mm each 2.91us
    pulse_time // 2 // 2.91 -> pulse_time // 5.82 -> pulse_time * 100 // 582
    """
    return __send_pulse_and_wait() * 100 // 582


def distance_cm():
    return (__send_pulse_and_wait() / 2) / 29.1


def deinit():
    global __TRIGGER_OBJ, __ECHO_OBJ
    trigger_pin, echo_pin = __init_HCSR04()
    trigger_pin.deinit()
    echo_pin.deinit()
    __TRIGGER_OBJ = None
    __ECHO_OBJ = None


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
    return pinmap_dump(['hcsrtrig', 'hcsrecho'])


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'distance_mm', 'distance_cm', 'deinit', 'pinmap'
