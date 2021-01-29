from sys import platform
__ADC = None


def __init_ADC():
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
            __ADC = ADC(get_pin_on_platform_by_key('adc_2'))
        else:
            __ADC = ADC(Pin(get_pin_on_platform_by_key('adc_2')))
    return __ADC


def measure():
    """
    TODO: Measure ADC value
    """
    value = __init_ADC().read()
    return "ADC value: {}".format(value)


def help():
    return 'measure'

