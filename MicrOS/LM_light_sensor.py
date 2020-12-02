"""
Source: https://how2electronics.com/temt6000-ambient-light-sensor-arduino-measure-light-intensity/
"""
from sys import platform
__ADC = None


def __init_tempt6000():
    """
    Setup ADC
    """
    global __ADC
    if __ADC is None:
        from machine import ADC, Pin
        from LogicalPins import get_pin_on_platform_by_key
        if 'esp8266' in platform:
            __ADC = ADC(get_pin_on_platform_by_key('adc_0'))
        else:
            __ADC = ADC(Pin(get_pin_on_platform_by_key('adc_0')))
            # set 11dB input attenuation (voltage range roughly 0.0v - 3.6v)
            __ADC.atten(ADC.ATTN_11DB)
            # set 9 bit return values (returned range 0-511)
            __ADC.width(ADC.WIDTH_9BIT)
    return __ADC


def light_intensity():
    """
    Measure light intensity in %
    """
    value = __init_tempt6000().read()
    light = value * 0.0976 #percentage calculation
    return {'light intensity [%]': light}


def measure_illuminance():
    """
    Measure light illuminance in flux
    """
    volts = __init_tempt6000().read() * 5.0 / 1024.0
    amps = volts / 10000.0      # across 10,000 Ohms
    microamps = amps * 1000000
    lux = microamps * 2.0
    return {'illuminance [lux]': lux}


def help():
    return 'intensity', 'illuminance', 'INFO sensor:TEMP600'

