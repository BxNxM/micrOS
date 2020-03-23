from machine import Pin, time_pulse_us
from time import sleep_us
from LogicalPins import getPlatformValByKey

def __init_HCSR04():
        trigger_pin = getPlatformValByKey('dist_trigger')
        echo_pin = getPlatformValByKey('dist_echo')
        # Init trigger pin (out)
        trigger_pin_obj = Pin(trigger_pin, mode=Pin.OUT, pull=None)
        trigger_pin_obj.value(0)
        # Init echo pin (in)
        echo_pin_obj = Pin(echo_pin, mode=Pin.IN, pull=None)
        return trigger_pin_obj, echo_pin_obj


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

def distance_mm():
        # To calculate the distance we get the pulse_time and divide it by 2
        # (the pulse walk the distance twice) and by 29.1 becasue
        # the sound speed on air (343.2 m/s), that It's equivalent to
        # 0.34320 mm/us that is 1mm each 2.91us
        # pulse_time // 2 // 2.91 -> pulse_time // 5.82 -> pulse_time * 100 // 582
        return __send_pulse_and_wait() * 100 // 582

def distance_cm():
        return (__send_pulse_and_wait() / 2) / 29.1

