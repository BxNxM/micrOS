"""
A MicroPython library for the TCS3472 light sensing chip
https://github.com/tti0/tcs3472-micropython

Copyright (c) 2021 tti0
Licensed under the MIT License
"""

from struct import unpack
from machine import I2C, Pin
from microIO import bind_pin, pinmap_search
from Types import resolve

from LM_neopixel import load as neo_load
from LM_neopixel import color as neo_color


class TCS3472:
    INSTANCE = None

    def __init__(self, address=0x29, led_pin=None):
        self._bus = I2C(sda=Pin(bind_pin('i2c_sda')), scl=Pin(bind_pin('i2c_scl')))
        self._i2c_address = address
        self._bus.writeto(self._i2c_address, b'\x80\x03')
        self._bus.writeto(self._i2c_address, b'\x81\x2b')
        self.led = Pin(bind_pin('led', led_pin), Pin.OUT)
        TCS3472.INSTANCE = self

    def scaled(self):
        crgb = self.raw()
        if crgb[0] > 0:
            return tuple(float(x) / crgb[0] for x in crgb[1:])
        return 0, 0, 0

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
    return {"rgb": sensor.rgb(), "light": sensor.light(), "brightness": sensor.brightness()}


def led(state=None):
    """
    SENSOR LED toggle
    :param state: None-automatic, True-ON, False-OFF
    """
    sensor = load()
    if state is None:
        s = sensor.led.value(not sensor.led.value())
    else:
        s = sensor.led.value(state)
    return "LED on" if s else "LED off"


def indicator(br=5):
    """
    Color indicator Neopixel LED update
    :param br: brightness 0-100
    """
    r, g, b = measure()['rgb']
    br = float(br / 100)
    r, g, b = int(r*br), int(g*br), int(b*br)
    return neo_color(r, g, b)


def send_color_update():
    """
    DEMO - Send color codes for all neomatrix devices over espnow
    """
    pass


def help(widgets=False):
    """
    TCS3472 Color sensor
    """
    return resolve(('load led_pin=20',
                    'measure',
                    'BUTTON led state=<True,False>',
                    'indicator br=<0-100>',
                    'pinmap'), widgets=widgets)
