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
            __ADC = ADC(get_pin_on_platform_by_key('adc_2'))
        else:
            __ADC = ADC(Pin(get_pin_on_platform_by_key('adc_2')))
            # set 11dB input attenuation (voltage range roughly 0.0v - 3.6v)
            __ADC.atten(ADC.ATTN_11DB)
            # set 9 bit return values (returned range 0-511)
            __ADC.width(ADC.WIDTH_9BIT)
    return __ADC


def measure():
    """
    TODO: Measure ADC value
    """
    value = __init_ADC().read()
    return "ADC value: {}".format(value)


def help():
    return 'measure'

