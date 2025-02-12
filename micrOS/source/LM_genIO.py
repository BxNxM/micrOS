from machine import Pin, PWM
from microIO import bind_pin, PinMap
from Common import SmartADC
from random import randint


#########################
#    PIN OBJ STORAGE    #
#########################

class IObjects:
    PIN_OBJS = {}
    DENY_TAG_INPUT = True

    @staticmethod
    def store_obj(pin:int, obj:object) -> None:
        IObjects.PIN_OBJS[pin] = obj

    @staticmethod
    def get_obj(pin:int) -> object:
        return IObjects.PIN_OBJS[pin]

    @staticmethod
    def is_unassigned(pin_number):
        return IObjects.PIN_OBJS.get(pin_number, None) is None

    @staticmethod
    def protect_builtins(pin_num, tag):
        if pin_num is None and IObjects.DENY_TAG_INPUT:
            raise Exception(f"pin must be integer not {type(tag)}: {tag}")


##################################
#     INTERNAL INIT FUNCTIONS    #
##################################

def __digital_out_init(pin):
    """
    Init Digital output
    """
    pin_tag, pin = (pin, None) if isinstance(pin, str) else (f"OUT{pin}", pin)
    IObjects.protect_builtins(pin, pin_tag)
    pin_num = bind_pin(pin_tag, pin)
    if IObjects.is_unassigned(pin_number=pin_num):
        pin_obj = Pin(pin_num, Pin.OUT)
        IObjects.store_obj(pin_num, pin_obj)
    return IObjects.get_obj(pin_num)


def __digital_in_init(pin):
    """
    Init Digital output
    """
    pin_tag, pin = (pin, None) if isinstance(pin, str) else (f"IN{pin}", pin)
    IObjects.protect_builtins(pin, pin_tag)
    pin_num = bind_pin(pin_tag, pin)
    if IObjects.is_unassigned(pin_number=pin_num):
        pin_obj = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        IObjects.store_obj(pin_num, pin_obj)
    return IObjects.get_obj(pin_num)


def __pwm_init(pin, freq):
    """
    Init PWM signal
    """
    pin_tag, pin = (pin, None) if isinstance(pin, str) else (f"PWM{pin}", pin)
    IObjects.protect_builtins(pin, pin_tag)
    pin_num = bind_pin(pin_tag, pin)
    if IObjects.is_unassigned(pin_number=pin_num):
        pin_obj = PWM(Pin(pin_num), freq=freq)
        IObjects.store_obj(pin_num, pin_obj)
    return IObjects.get_obj(pin_num)


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
    pin_tag, pin = (pin, None) if isinstance(pin, str) else (f"ADC{pin}", pin)
    IObjects.protect_builtins(pin, pin_tag)
    pin = bind_pin(pin_tag, pin)
    data = SmartADC.get_instance(pin).get()
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


def load(allow_tags=False):
    """
    Optional load function to set
    tag input besides pin numbers.
    [WARNING] allow_tag=True can be dangerous
    - it can overwrite existing I/O based on
    the provided tag
    :param allow_tag: default False
    """
    IObjects.DENY_TAG_INPUT = not allow_tags
    return "[WARNING] allow_tag=True can be dangerous, use it consciously!!!" if allow_tags else "Loaded"


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
           'get_in pin',\
           'load allow_tags=False'
