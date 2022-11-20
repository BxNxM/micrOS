from time import sleep
from LogicalPins import physical_pin, pinmap_dump
from Common import SmartADC

"""
https://cimpleo.com/blog/simple-arduino-ph-meter/
ADC.ATTN_0DB — the full range voltage: 1.2V
ADC.ATTN_2_5DB — the full range voltage: 1.5V
ADC.ATTN_6DB — the full range voltage: 2.0V
ADC.ATTN_11DB — the full range voltage: 3.3V
"""


def __measure(samples=10):
    adc_obj = SmartADC.get_singleton(physical_pin('ph'))
    mbuf = 0
    for k in range(0, samples):
        mbuf += adc_obj.get()['volt']
        sleep(0.1)
    voltage = round(mbuf / samples, 3)
    return voltage


def measure():
    data = SmartADC.get_singleton(physical_pin('ph')).get()
    return "ADC data: {}\nAVG V: {}".format(data, __measure())


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
    return pinmap_dump('ph')


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'measure', 'pinmap'

