from time import sleep
from LogicalPins import physical_pin, pinmap_dump
from Common import SmartADC


class Data:
    TIMER_SEC = 60


def motion_trigger():
    """
    Set motion trigger by IRQx - PIR sensor
    """
    pass


def noise(threshold=50):
    """
    ADC microphone measurement
    - handle threshold value
    """
    adc_obj = SmartADC.get_singleton(physical_pin('mic'))
    data = adc_obj.get()                # raw, percent, volt
    voltage = data['percent']
    return voltage


#######################
# LM helper functions #
#######################

def pinmap():
    # Return module used PIN mapping
    return pinmap_dump('mic')


def help():
    return 'motion_trigger', 'noise', 'pinmap'

