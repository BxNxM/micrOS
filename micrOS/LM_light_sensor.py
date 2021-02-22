"""
Source: https://how2electronics.com/temt6000-ambient-light-sensor-arduino-measure-light-intensity/
ADC.ATTN_0DB — the full range voltage: 1.2V
ADC.ATTN_2_5DB — the full range voltage: 1.5V
ADC.ATTN_6DB — the full range voltage: 2.0V
ADC.ATTN_11DB — the full range voltage: 3.3V
"""
from sys import platform
__ADC = None
__ADC_RES = 1024


def __init_tempt6000():
    """
    Setup ADC
    read        0(0V)-1024(1,2V) MAX 1V input on esp8266
    read        0(0V)-1024(1,2-3,3V) input on esp32 (based on settings)
    read_u16    0 - 65535 range
    """
    global __ADC, __ADC_RES
    if __ADC is None:
        from machine import ADC, Pin
        from LogicalPins import get_pin_on_platform_by_key
        if 'esp8266' in platform:
            __ADC = ADC(get_pin_on_platform_by_key('temp6000'))
            __ADC_RES = 1023                # Resolution on esp8266
        else:
            __ADC = ADC(Pin(get_pin_on_platform_by_key('temp6000')))
            __ADC.atten(ADC.ATTN_11DB)      # 0 - 3,3V sampling range
            __ADC_RES = 4095                # Resolution on esp32
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
    volts = __init_tempt6000().read() * 5.0 / __ADC_RES    # read a raw analog value in the range 0-ADC_RES
    amps = volts / 10000.0                                 # across 10,000 Ohms
    microamps = amps * 1000000
    lux = '{:.2f}'.format(microamps * 2.0)
    return {'illuminance [lux]': lux}


def help():
    return 'intensity', 'illuminance', 'INFO sensor:TEMP600'

