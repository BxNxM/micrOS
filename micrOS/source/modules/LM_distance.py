from machine import Pin, time_pulse_us
from utime import sleep_us
from microIO import bind_pin, pinmap_search
from Common import micro_task
from Types import resolve

__TRIGGER_OBJ = None
__ECHO_OBJ = None


def __init_HCSR04():
    """
    HCSR04 Ultrasonic distance sensor
    """
    global __TRIGGER_OBJ, __ECHO_OBJ
    if __TRIGGER_OBJ is None or __ECHO_OBJ is None:
        trigger_pin = bind_pin('hcsrtrig')
        echo_pin = bind_pin('hcsrecho')
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


async def __task(period_ms, dimmer, idle_cm):
    average = None
    with micro_task(tag="distance.visual") as my_task:
        while True:
            brightness_max_cm = 200
            brightness_min_cm = 5
            dist = int(measure_cm()["cm"])
            if dist > idle_cm+100:
                await my_task.feed(sleep_ms=50)
                continue
            dist = brightness_max_cm if dist > brightness_max_cm else dist   # Limit max
            dist = 0 if dist < brightness_min_cm else dist                   # Limit min
            average = dist if average is None else (average + dist) / 2
            brightness = int(600 * (average/(brightness_max_cm)))
            if dist >= idle_cm:
                dimmer(5)
            else:
                dimmer(brightness)

            # Store data in task cache (task show mytask)
            my_task.out = f'Dist: {dist} br: {brightness}'
            # Async sleep - feed event loop
            await my_task.feed(sleep_ms=period_ms)


def start_dimmer_indicator(idle_distance=180):
    """Distance visualization on LED brightness (LM_dimmer)"""
    from LM_dimmer import set_value
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    state = micro_task(tag="distance.visual", task=__task(period_ms=200, dimmer=set_value, idle_cm=idle_distance))
    return "Starting" if state else "Already running"



#########################
# Application functions #
#########################

def load():
    """
    Initialize HCSR04 ultrasonic distance sensor module
    """
    __init_HCSR04()
    return "HCSR04 Ultrasonic distance sensor - loaded"


def measure_mm():
    """
    To calculate the distance we get the pulse_time and divide it by 2
    (the pulse walk the distance twice) and by 29.1 becasue
    the sound speed on air (343.2 m/s), that It's equivalent to
    0.34320 mm/us that is 1mm each 2.91us
    pulse_time // 2 // 2.91 -> pulse_time // 5.82 -> pulse_time * 100 // 582
    """
    return {'mm': __send_pulse_and_wait() * 100 // 582}


def measure_cm():
    return {'cm': (__send_pulse_and_wait() / 2) / 29.1}


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
    return pinmap_search(['hcsrtrig', 'hcsrecho', 'dimmer'])


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('measure_mm', 'TEXTBOX measure_cm', 'deinit', 'pinmap',
                             'load', 'start_dimmer_indicator idle_distance=180',
                             '[info] HCSR04 Ultrasonic distance sensor'), widgets=widgets)
