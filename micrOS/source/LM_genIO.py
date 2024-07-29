from machine import Pin, PWM
from microIO import resolve_pin, register_pin, PinMap
from Common import SmartADC
from random import randint


#########################
#    PIN OBJ STORAGE    #
#########################

class IObjects:
    PIN_OBJS = {}

    @staticmethod
    def store_obj(pin, obj):
        IObjects.PIN_OBJS[pin] = obj

    @staticmethod
    def get_obj(pin):
        return IObjects.PIN_OBJS[pin]


##################################
#     INTERNAL INIT FUNCTIONS    #
##################################

def __digital_out_init(pin):
    """
    Init Digital output
    """
    if not isinstance(pin, int):
        pin = resolve_pin(pin)

    # Register pin in microIO (drops exception if pin already booked)
    pin_tag = f"OUT{pin}"
    if PinMap.IO_USE_DICT.get(pin_tag, None) is None:
        pin = register_pin(pin_tag, pin)
        pin_obj = Pin(pin, Pin.OUT)
        IObjects.store_obj(pin, pin_obj)
    return IObjects.get_obj(pin)


def __digital_in_init(pin):
    """
    Init Digital output
    """
    if not isinstance(pin, int):
        pin = resolve_pin(pin)

    # Register pin in microIO (drops exception if pin already booked)
    pin_tag = f"IN{pin}"
    if PinMap.IO_USE_DICT.get(pin_tag, None) is None:
        pin = register_pin(pin_tag, pin)
        pin_obj = Pin(pin, Pin.IN, Pin.PULL_UP)
        IObjects.store_obj(pin, pin_obj)
    return IObjects.get_obj(pin)


def __pwm_init(pin, freq):
    """
    Init PWM signal
    """
    if not isinstance(pin, int):
        pin = resolve_pin(pin)

    # Register pin in microIO (drops exception if pin already booked)
    pin_tag = f"PWM{pin}"
    if PinMap.IO_USE_DICT.get(pin_tag, None) is None:
        pin = register_pin(pin_tag, pin)
        pin_obj = PWM(Pin(pin), freq=freq)
        IObjects.store_obj(pin, pin_obj)
    return IObjects.get_obj(pin)


##################################
#   GENERAL INTERFACE FUNCTIONS  #
##################################

def set_pwm(pin, duty=500, freq=20480):
    """
    Set PWM signal output
    :param pin: pin number or logical name
    :param duty: pwm duty
    :param freq: pwm frequency (board dependent)
    :return dict: pin, freq, duty
    """
    __pwm_init(pin, freq).duty(duty)
    return {'pin': pin, 'freq': freq, 'duty': duty}


def set_random_pwm(pin, min_duty, max_duty, freq=20480):
    """
    Set random PWM duty in min-max range
    :param pin: pin number or logical name
    :param min_duty: set min duty value (0-1000)
    :param max_duty: set max duty value (0-1000)
    :param freq: pwm frequency (board dependent)
    """
    value = randint(min_duty, max_duty)
    return set_pwm(pin, duty=value, freq=freq)


def set_out(pin, state=None):
    """
    Set simple digital (high/low) output
    :param pin: pun number or logical name
    :param state: state: 1/0 = True/False
    :return dict: pin, state
    """
    obj = __digital_out_init(pin)
    if state is None:
        state = not obj.value()
    obj.value(state)
    return {'pin': pin, 'state': state}


def get_adc(pin, key=None):
    """
    Get Analog Digital conersion input
    :param pin: pin number or logical pin name
    :param key: select adc parameter by key
    :return dict: adc volt, percent, raw
    """
    if isinstance(pin, int):
        pin_tag = f"ADC{pin}"
        pin = register_pin(pin_tag, pin)
    data = SmartADC.get_singleton(pin).get()
    data["pin"] = pin
    if key is None:
        return data
    return data.get(key, None)


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

def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'set_pwm pin=<int> duty=<0-1000> freq=<int>',\
           'set_random_pwm pin min_duty max_duty freq=20480)',\
           'set_out pin=<int> state=<None/True/False>',\
           'get_adc pin key=None',\
           'get_in pin'
