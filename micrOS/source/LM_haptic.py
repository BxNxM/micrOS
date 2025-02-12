from microIO import bind_pin, pinmap_search
from Types import resolve
from machine import Pin, PWM
from utime import sleep_ms

class Haptic:
    HAPTIC_OBJ = None
    # Haptic vibration motor settings
    LOW = 700
    HIGH = 1000
    STOP = 0
    WAIT_TO_STOP_MS = 100
    INTENSITY = "low"

def load(intensity=None):
    """
    Init haptic engine
    :param intensity: low / high / None haptic feedback intensity
    """
    if Haptic.HAPTIC_OBJ is None:
        dimmer_pin = Pin(bind_pin('haptic'))
        Haptic.HAPTIC_OBJ = PWM(dimmer_pin, freq=20480)
        Haptic.HAPTIC_OBJ.duty(0)
    if intensity in ("high", "low"):
        Haptic.INTENSITY = intensity
    return Haptic.HAPTIC_OBJ


def tap():
    """
    Tap - buzz effect
    """
    haptic = load()
    if Haptic.INTENSITY == "low":
        haptic.duty(Haptic.LOW)
        sleep_ms(150)
        haptic.duty(Haptic.STOP)
        return "Tap: low"
    if Haptic.INTENSITY == "high":
        haptic.duty(Haptic.HIGH)
        sleep_ms(150)
        haptic.duty(Haptic.STOP)
        return "Tap: high"

def gen(intensity=Haptic.LOW, wait=200, stop_wait=100, repeat=2):
    """
    Generate effect
    :param intensity: 600-1000
    :param wait: wait after intensity was set [ms]
    :param stop_wait: wait for top the motor [ms]
    :param repeat: repeat cycle
    """
    haptic = load()
    for _ in range(repeat):
        # Wait to run
        haptic.duty(intensity)
        sleep_ms(wait)
        # Wait to stop
        haptic.duty(0)
        sleep_ms(stop_wait)
    haptic.duty(0)
    return f"finished: {(wait+stop_wait)*repeat}ms:{intensity}:{wait}:{repeat}"


def effect1():
    haptic = load()
    haptic.duty(Haptic.HIGH)
    sleep_ms(150)
    haptic.duty(Haptic.LOW)
    sleep_ms(100)
    haptic.duty(Haptic.HIGH)
    sleep_ms(100)
    haptic.duty(Haptic.STOP)
    return "finished: 350ms"


def effect2():
    haptic = load()
    haptic.duty(Haptic.HIGH)
    sleep_ms(150)
    for i in range(Haptic.HIGH, 300, -100):
        haptic.duty(i)
        sleep_ms(50)
    haptic.duty(Haptic.STOP)
    return "finished: 400ms"


def deinit():
    Haptic.HAPTIC_OBJ.deinit()
    Haptic.HAPTIC_OBJ = None
    return "Deinited"


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_search('haptic')


def help(widgets=False):
    return resolve(("load intensity='low/high'/None",
                             "BUTTON tap",
                             "BUTTON effect1",
                             "BUTTON effect2",
                             "gen max=<600-1000> wait=200 stop_wait=100 repeat=2",
                             "deinit",
                             "pinmap"), widgets=widgets)
