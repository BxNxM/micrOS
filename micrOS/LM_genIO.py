from machine import Pin, PWM, ADC
from sys import platform
from LogicalPins import get_pin_on_platform_by_key
__ADC_PROP = (1023, 1.0)

"""
ADC.ATTN_0DB: 0dB attenuation, gives a maximum input voltage of 1.00v - this is the default configuration
ADC.ATTN_2_5DB: 2.5dB attenuation, gives a maximum input voltage of approximately 1.34v
ADC.ATTN_6DB: 6dB attenuation, gives a maximum input voltage of approximately 2.00v
ADC.ATTN_11DB: 11dB attenuation, gives a maximum input voltage of approximately 3.6v
"""


def __digital_out_init(pin):
    """
    Init Digital output
    """
    if not isinstance(pin, int):
        pin = get_pin_on_platform_by_key(pin)
    return Pin(pin, Pin.OUT)


def __digital_in_init(pin):
    """
    Init Digital output
    """
    if not isinstance(pin, int):
        pin = get_pin_on_platform_by_key(pin)
    return Pin(pin, Pin.IN, Pin.PULL_UP)


def __pwm_init(pin, freq):
    """
    Init PWM signal
    """
    if not isinstance(pin, int):
        pin = get_pin_on_platform_by_key(pin)
    if platform == 'esp8266':
        return PWM(pin, freq=freq)
    return PWM(Pin(pin), freq=freq)


def __init_adc(pin):
    """
    Init ADC
    """
    global __ADC_PROP
    if not isinstance(pin, int):
        pin = get_pin_on_platform_by_key(pin)
    if 'esp8266' in platform:
        adc = ADC(pin)          # 1V measure range
        __ADC_PROP = (1023, 1.0)
    else:
        adc = ADC(Pin(pin))
        adc.atten(ADC.ATTN_11DB)                          # 3.3V measure range
        __ADC_PROP = (4095, 3.6)
    return adc


def set_pwm(pin, freq=1024, duty=500):
    """
    Set PWM signal output
    :param pin: pin number or logical name
    :param freq: pwm frequency (board dependent)
    :param duty: pwm duty
    :return: verdict
    """
    __pwm_init(pin, freq).duty(duty)
    return {'pin': pin, 'freq': freq, 'duty': duty}


def set_out(pin, state):
    """
    Set simple digital (high/low) output
    :param pin: pun number or logical name
    :param state: state: 1/0 = True/False
    :return: verdict
    """
    __digital_out_init(pin).value(state)
    return {'pin': pin, 'state': state}


def get_adc(pin):
    """
    Get Analog Digital conersion input
    :param pin: pin number or logical pin name
    :return: verdict
    """
    raw_value = __init_adc(pin).read()
    return {'raw': raw_value, 'pin': pin}


def get_in(pin):
    """
    Get digital input (high(1)/ low (0))
    :param pin: pin number or logical pin
    :return: verdict
    """
    return {'pin': pin, 'state': __digital_in_init(pin).value()}


#######################
# LM helper functions #
#######################

def help():
    return 'set_pwm pin=<int> freq=<int> duty=<0-1000>', 'set_out pin state', 'get_adc pin', 'get_in pin'
