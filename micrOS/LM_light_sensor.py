"""
Source: https://how2electronics.com/temt6000-ambient-light-sensor-arduino-measure-light-intensity/
"""
from sys import platform
__ADC = None


def __init_tempt6000():
    """
    Setup ADC
    read        0(0V)-1024(1V) MAX 1V input
    read_u16    0 - 65535 range
    """
    global __ADC
    if __ADC is None:
        from machine import ADC, Pin
        from LogicalPins import get_pin_on_platform_by_key
        if 'esp8266' in platform:
            __ADC = ADC(get_pin_on_platform_by_key('temp6000'))
        else:
            __ADC = ADC(Pin(get_pin_on_platform_by_key('temp6000')))
    return __ADC


def intensity():
    """
    Measure light intensity in %
    max value: 65535
    """
    value = __init_tempt6000().read_u16()
    percent = '{:.2f}'.format((value / 65535) * 100)
    return {'light intensity [%]': percent}


def illuminance():
    """
    Measure light illuminance in flux
    """
    volts = __init_tempt6000().read() * 5.0 / 1024.0    # read a raw analog value in the range 0-1024
    amps = volts / 10000.0                              # across 10,000 Ohms
    microamps = amps * 1000000
    lux = '{:.2f}'.format(microamps * 2.0)
    return {'illuminance [lux]': lux}


def help():
    return 'intensity', 'illuminance', 'INFO sensor:TEMP600'

