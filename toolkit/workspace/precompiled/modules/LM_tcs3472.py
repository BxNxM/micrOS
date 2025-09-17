"""
A MicroPython library for the TCS3472 light sensing chip
https://github.com/tti0/tcs3472-micropython

Copyright (c) 2021 tti0
Licensed under the MIT License
"""

from struct import unpack
from time import sleep
from machine import I2C, Pin, PWM
from microIO import bind_pin, pinmap_search
from Types import resolve

from LM_neopixel import load as neo_load, color as neo_color    # local neopixel light indicator
from LM_cluster import run as cluster_run                       # DEMO: neomatrix cluster

CURRENT_ANIMATION_INDEX = 0                                     # DEMO: neomatrix cluster animation

class TCS3472:
    INSTANCE = None

    def __init__(self, address=0x29, led_pin=None):
        self._bus = I2C(sda=Pin(bind_pin('i2c_sda')), scl=Pin(bind_pin('i2c_scl')))
        self._i2c_address = address
        self._bus.writeto(self._i2c_address, b'\x80\x03')
        self._bus.writeto(self._i2c_address, b'\x81\x2b')
        self.led = PWM(Pin(bind_pin('led', led_pin), Pin.OUT), freq=20480)
        self.led_brightness = 30
        TCS3472.INSTANCE = self

    def scaled(self, saturation=1.5):
        """
        Normalize by strongest color, then adjust saturation.
        saturation = 1.0 -> normal
        saturation > 1.0 -> more vibrant
        saturation < 1.0 -> more pastel
        """
        _, r, g, b = self.raw()
        m = max(r, g, b)
        if m == 0:
            return 0.0, 0.0, 0.0

        # Normalize by strongest channel
        r, g, b = r / m, g / m, b / m

        # Grayscale = average of channels
        gray = (r + g + b) / 3

        # Interpolate between gray and color
        r = gray + (r - gray) * saturation
        g = gray + (g - gray) * saturation
        b = gray + (b - gray) * saturation

        # Clamp to 0..1
        return max(0, min(1, r)), max(0, min(1, g)), max(0, min(1, b))

    def rgb(self):
        return tuple(int(x * 255) for x in self.scaled())

    def light(self):
        return self.raw()[0]

    def brightness(self, level=65.535):
        return int((self.light() / level))

    def valid(self):
        self._bus.writeto(self._i2c_address, b'\x93')
        return self._bus.readfrom(self._i2c_address, 1)[0] & 1

    def raw(self):
        self._bus.writeto(self._i2c_address, b'\xb4')
        return unpack("<HHHH", self._bus.readfrom(self._i2c_address, 8))


############################ Exposed functions ############################

def load(led_pin=20):
    """
    Load the TCS3472 Color sensor instance.
    """
    if TCS3472.INSTANCE is None:
        TCS3472(led_pin=led_pin)
        neo_load(ledcnt=1)
        led(False)
    return TCS3472.INSTANCE


def pinmap():
    """
    Show used pin mapping for this module.
    """
    return pinmap_search(['i2c_scl', 'i2c_sda', 'led'])


def measure():
    """
    MEASURE sensor
    """
    sensor = load()
    sensor.led.duty(int(sensor.led_brightness * 10))
    sleep(0.4)
    measurement = {"rgb": sensor.rgb(), "light": sensor.light(), "brightness": sensor.brightness()}
    sleep(0.1)
    sensor.led.duty(0)
    return measurement


def led(state:bool=None, br:int=None):
    """
    SENSOR LED toggle
    :param state: None-automatic, True-ON, False-OFF
    :param br: brightness 0-100
    """
    def _set_duty(_br):
        _br = sensor.led_brightness if _br is None else _br
        sensor.led.duty(int(_br * 10))
        if _br != 0:
            sensor.led_brightness = _br

    sensor = load()
    if state is None:
        # INVERT STATE
        led_current_state = sensor.led.duty() > 0
        if led_current_state:
            _set_duty(br)
            _set_duty(0)
        else:
            _set_duty(br)
    else:
        # SET STATE: ON/OFF
        if state:
            _set_duty(br)
        else:
            _set_duty(br)
            _set_duty(0)
    return f"LED on, {sensor.led_brightness}%" if sensor.led.duty()>0 else f"LED off"


def indicator(br=5):
    """
    Color indicator Neopixel LED update
    :param br: brightness 0-100
    """
    r, g, b = measure()['rgb']
    br = float(br / 100)
    _r, _g, _b = int(r*br), int(g*br), int(b*br)
    neo_color(_r, _g, _b, smooth=False)
    return r, g, b


def neomatrix_update():
    """
    DEMO - Send color codes for all neomatrix devices over espnow cluster
    """
    r, g, b = indicator()
    command = f"neomatrix color_fill {r} {g} {b}"
    cluster_run(command)
    return {"cmd": command, "cluster": "task show con.espnow.*"}


def neomatrix_animation():
    """
    DEMO - Set random animation on neomatrix espnow cluster
    """
    global CURRENT_ANIMATION_INDEX
    animations = ('spiral', 'snake', 'noise')

    next_animation = CURRENT_ANIMATION_INDEX + 1
    CURRENT_ANIMATION_INDEX = 0 if next_animation >= len(animations) else next_animation
    command = f"neomatrix {animations[CURRENT_ANIMATION_INDEX]}"
    cluster_run(command)
    return {"cmd": command, "cluster": "task show con.espnow.*"}


def help(widgets=False):
    """
    TCS3472 Color sensor
    """
    return resolve(('load led_pin=20',
                    'TEXTBOX measure',
                    'BUTTON led state=<True,False>',
                    'SLIDER led state=True br=<0-100-5>',
                    'indicator br=<0-100>',
                    'BUTTON neomatrix_update',
                    'BUTTON neomatrix_animation',
                    'pinmap'), widgets=widgets)
