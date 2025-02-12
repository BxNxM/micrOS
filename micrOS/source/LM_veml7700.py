# Copyright (c) 2019 Joseph Hopfmüller
# This module is a fork of Christophe Rousseaus module.
# see: https://github.com/palouf34/veml7700.git

from machine import SoftI2C, Pin
from time import sleep
from micropython import const
from microIO import bind_pin, pinmap_search
from Types import resolve

# start const
# default address
addr = const(0x10)

# Write registers
als_conf_0 = const(0x00)
als_WH = const(0x01)
als_WL = const(0x02)
pow_sav = const(0x03)

# Read registers
als = const(0x04)
white = const(0x05)
interrupt = const(0x06)

# gain            0.125                    0.25                    1                        2                         integration time
confValues = {25: {1 / 8: bytearray([0x00, 0x13]), 1 / 4: bytearray([0x00, 0x1B]), 1: bytearray([0x00, 0x01]),
                   2: bytearray([0x00, 0x0B])},  # 25
              50: {1 / 8: bytearray([0x00, 0x12]), 1 / 4: bytearray([0x00, 0x1A]), 1: bytearray([0x00, 0x02]),
                   2: bytearray([0x00, 0x0A])},  # 50
              100: {1 / 8: bytearray([0x00, 0x10]), 1 / 4: bytearray([0x00, 0x18]), 1: bytearray([0x00, 0x00]),
                    2: bytearray([0x00, 0x08])},  # 100
              200: {1 / 8: bytearray([0x40, 0x10]), 1 / 4: bytearray([0x40, 0x18]), 1: bytearray([0x40, 0x00]),
                    2: bytearray([0x40, 0x08])},  # 200
              400: {1 / 8: bytearray([0x80, 0x10]), 1 / 4: bytearray([0x80, 0x18]), 1: bytearray([0x80, 0x00]),
                    2: bytearray([0x80, 0x08])},  # 400
              800: {1 / 8: bytearray([0xC0, 0x10]), 1 / 4: bytearray([0xC0, 0x18]), 1: bytearray([0xC0, 0x00]),
                    2: bytearray([0xC0, 0x08])}}  # 800

# gain               0.125,  0.25,   1,      2       integration time
gainValues = {25: {1 / 8: 1.8432, 1 / 4: 0.9216, 1: 0.2304, 2: 0.1152},  # 25
              50: {1 / 8: 0.9216, 1 / 4: 0.4608, 1: 0.1152, 2: 0.0576},  # 50
              100: {1 / 8: 0.4608, 1 / 4: 0.2304, 1: 0.0288, 2: 0.0144},  # 100
              200: {1 / 8: 0.2304, 1 / 4: 0.1152, 1: 0.0288, 2: 0.0144},  # 200
              400: {1 / 8: 0.1152, 1 / 4: 0.0576, 1: 0.0144, 2: 0.0072},  # 400
              800: {1 / 8: 0.0876, 1 / 4: 0.0288, 1: 0.0072, 2: 0.0036}}  # 800

# fin des constante

# Reference data sheet Table 1 for configuration settings

interrupt_high = bytearray([0x00, 0x00])  # Clear values
# Reference data sheet Table 2 for High Threshold

interrupt_low = bytearray([0x00, 0x00])  # Clear values
# Reference data sheet Table 3 for Low Threshold

power_save_mode = bytearray([0x00, 0x00])  # clear values


# Reference data sheet Table 4 for Power Saving Modes


class VEML7700:
    INSTANCE = None

    def __init__(self,
                 address=addr,
                 i2c=None,
                 it=25,
                 gain=1 / 8,
                 **kwargs):

        self.address = address
        if i2c is None:
            raise ValueError('An I2C object is required.')
        self.i2c = i2c
        VEML7700.INSTANCE = self

        confValuesForIt = confValues.get(it)
        gainValuesForIt = gainValues.get(it)
        if confValuesForIt is not None and gainValuesForIt is not None:
            confValueForGain = confValuesForIt.get(gain)
            gainValueForGain = gainValuesForIt.get(gain)
            if confValueForGain is not None and gainValueForGain is not None:
                self.confValues = confValueForGain
                self.gain = gainValueForGain
            else:
                raise ValueError('Wrong gain value. Use 1/8, 1/4, 1, 2')
        else:
            raise ValueError('Wrong integration time value. Use 25, 50, 100, 200, 400, 800')

        self.init()

    def init(self):

        # load calibration data
        # self.i2c.writeto_mem(self.address, als_conf_0, bytearray([0x00,0x13]) )
        self.i2c.writeto_mem(self.address, als_conf_0, self.confValues)
        self.i2c.writeto_mem(self.address, als_WH, interrupt_high)
        self.i2c.writeto_mem(self.address, als_WL, interrupt_low)
        self.i2c.writeto_mem(self.address, pow_sav, power_save_mode)

    def detect(self):
        """ Functions is  verified is  module has detecedself.

        this function not implemented for this time
        """
        None

    def read_lux(self):
        """ Reads the data from the sensor and returns the data.

            Returns:
               the number of lux detect by this captor.
        """
        # The frequency to read the sensor should be set greater than
        # the integration time (and the power saving delay if set).
        # Reading at a faster frequency will not cause an error, but
        # will result in reading the previous data

        self.lux = bytearray(2)

        sleep(.04)  # 40ms

        self.i2c.readfrom_mem_into(self.address, als, self.lux)
        self.lux = self.lux[0] + self.lux[1] * 256
        self.lux = self.lux * self.gain
        return (int(round(self.lux, 0)))


def load():
    """
    VEML7700 Digital light intensity sensor
    """
    if VEML7700.INSTANCE is None:
        i2c = SoftI2C(Pin(bind_pin('i2c_scl')), Pin(bind_pin('i2c_sda')))
        VEML7700.INSTANCE = VEML7700(address=0x10, i2c=i2c, it=100, gain=1/8)
    return VEML7700.INSTANCE


def read_lux():
    """Read LUX value"""
    lux = load().read_lux()
    return {"LUX": lux}


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_search(['i2c_scl', 'i2c_sda'])


def help(widgets=False):
    return resolve(('load', 'TEXTBOX read_lux', 'pinmap', '[info] Digital light intensity sensor'), widgets=widgets)