from machine import Pin, PWM
from sys import platform
from LogicalPins import physical_pin
from Common import SmartADC


def __digital_out_init(pin):
    """
    Init Digital output
    """
    if not isinstance(pin, int):
        pin = physical_pin(pin)
    return Pin(pin, Pin.OUT)


def __digital_in_init(pin):
    """
    Init Digital output
    """
    if not isinstance(pin, int):
        pin = physical_pin(pin)
    return Pin(pin, Pin.IN, Pin.PULL_UP)


def __pwm_init(pin, freq):
    """
    Init PWM signal
    """
    if not isinstance(pin, int):
        pin = physical_pin(pin)
    if platform == 'esp8266':
        return PWM(pin, freq=freq)
    return PWM(Pin(pin), freq=freq)


def set_pwm(pin, freq=1024, duty=500):
    """
    Set PWM signal output
    :param pin: pin number or logical name
    :param freq: pwm frequency (board dependent)
    :param duty: pwm duty
    :return dict: pin, freq, duty
    """
    __pwm_init(pin, freq).duty(duty)
    return {'pin': pin, 'freq': freq, 'duty': duty}


def set_out(pin, state):
    """
    Set simple digital (high/low) output
    :param pin: pun number or logical name
    :param state: state: 1/0 = True/False
    :return dict: pin, state
    """
    __digital_out_init(pin).value(state)
    return {'pin': pin, 'state': state}


def get_adc(pin):
    """
    Get Analog Digital conersion input
    :param pin: pin number or logical pin name
    :return dict: adc volt, percent, raw
    """
    data = SmartADC.get_singleton(pin).get()
    data["pin"] = pin
    return data


def get_in(pin):
    """
    Get digital input (high(1)/ low (0))
    :param pin: pin number or logical pin
    :return dict: pin, state
    """
    return {'pin': pin, 'state': __digital_in_init(pin).value()}


#######################
# LM helper functions #
#######################

def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'set_pwm pin=<int> freq=<int> duty=<0-1000>', 'set_out pin state', 'get_adc pin', 'get_in pin'
