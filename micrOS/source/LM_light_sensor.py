"""
Source: https://how2electronics.com/temt6000-ambient-light-sensor-arduino-measure-light-intensity/
ADC.ATTN_0DB — the full range voltage: 1.2V
ADC.ATTN_2_5DB — the full range voltage: 1.5V
ADC.ATTN_6DB — the full range voltage: 2.0V
ADC.ATTN_11DB — the full range voltage: 3.3V
"""
from LogicalPins import physical_pin, pinmap_dump
from Common import SmartADC

ADC = None


def __init_tempt6000():
    """
    Setup ADC
    """
    global ADC
    if ADC is None:
        ADC = SmartADC(physical_pin('temp6000'))
    return ADC


def intensity():
    """
    Measure light intensity in %
    """
    percent = __init_tempt6000().get()['percent']
    return {'light intensity [%]': percent}


def illuminance():
    """
    Measure light illuminance in flux
    """
    volts = __init_tempt6000().get()['volt']
    amps = volts / 10000.0                    # across 10,000 Ohms (voltage divider circuit)
    microamps = amps * 1000000
    lux = '{:.2f}'.format(microamps * 2.0)
    return {'illuminance [lux]': lux}


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
    return pinmap_dump('temp6000')


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'intensity', 'illuminance', 'pinmap', 'INFO sensor:TEMP600'

