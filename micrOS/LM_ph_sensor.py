from machine import ADC, Pin
from sys import platform
from time import sleep
from LogicalPins import get_pin_on_platform_by_key
__ADC = None
# [0] ADC RESOLUTION, [1] ADC VOLTAGE MEASURE RANGE
__ADC_PROP = (1023, 1.0)

"""
https://cimpleo.com/blog/simple-arduino-ph-meter/
ADC.ATTN_0DB — the full range voltage: 1.2V
ADC.ATTN_2_5DB — the full range voltage: 1.5V
ADC.ATTN_6DB — the full range voltage: 2.0V
ADC.ATTN_11DB — the full range voltage: 3.3V
"""


def __init_ADC():
    """
    Setup ADC
    read        0(0V)-1024(1,2-3,3V)
    """
    global __ADC, __ADC_PROP
    if __ADC is None:
        if 'esp8266' in platform:
            __ADC = ADC(get_pin_on_platform_by_key('ph'))       # 1V measure range
            __ADC_PROP = (1023, 1.0)
        else:
            __ADC = ADC(Pin(get_pin_on_platform_by_key('ph')))
            __ADC.atten(ADC.ATTN_11DB)                          # 3.6V measure range
            __ADC.width(ADC.WIDTH_10BIT)                        # Default 10 bit ADC
            __ADC_PROP = (1023, 3.6)
    return __ADC


def __measure(samples=10):
    mbuf = 0
    for k in range(0, samples):
        mbuf += __init_ADC().read()
        sleep(0.1)
    voltage = __ADC_PROP[1] / __ADC_PROP[0] * (mbuf/samples)
    ph = 7 + ((2.5 - voltage) / 0.18)
    return ph


def measure():
    raw_value = __init_ADC().read()
    return "ADC value: {}/{}\nPH: {}".format(raw_value, __ADC_PROP, __measure())


#######################
# LM helper functions #
#######################

def help():
    return 'measure'

