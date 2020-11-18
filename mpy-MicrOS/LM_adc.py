from time import sleep
from sys import platform
__ADC = None


def __init_ADC():
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


def measure():
    """
    Measure ADC value
    """
    value = __init_ADC().read()
    return "ADC value: {}".format(value)


def action_fltr(limit=20, threshold=1):
    """
    Evaluate input trigger action
    return: bool
    """
    if __init_ADC().read() > limit:
        sleep(threshold)
        return True
    return False


def help():
    return 'measure', '(bool)action_fltr(limit=<0-1000>, threshold=<sec>'

