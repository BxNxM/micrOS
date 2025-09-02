"""
A MicroPython library for the TCS3472 light sensing chip
https://github.com/tti0/tcs3472-micropython

Copyright (c) 2021 tti0
Licensed under the MIT License
"""

from machine import I2C, Pin
from microIO import bind_pin, pinmap_search
import struct


class TCS3472:
    INSTANCE = None

    def __init__(self, bus, address=0x29):
        self._bus = bus
        self._i2c_address = address
        self._bus.writeto(self._i2c_address, b'\x80\x03')
        self._bus.writeto(self._i2c_address, b'\x81\x2b')
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
        return struct.unpack("<HHHH", self._bus.readfrom(self._i2c_address, 8))


############################ Exposed functions ############################

def load():
    """
    Load the TCS3472 Color sensor instance.
    """
    if TCS3472.INSTANCE is None:
        bus = I2C(sda=Pin(bind_pin('i2c_sda')), scl=Pin(bind_pin('i2c_scl')))
        TCS3472.INSTANCE = TCS3472(bus)
    return TCS3472.INSTANCE


def pinmap():
    return pinmap_search(['i2c_scl', 'i2c_sda'])


def measure():
    sensor = load()
    return {"rgb": sensor.rgb(), "light": sensor.light(), "brightness": sensor.brightness()}


def help(widgest=False):
    """
    TCS3472 Color sensor
    """
    return 'load', 'measure'
