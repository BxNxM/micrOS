from microIO import physical_pin, pinmap_dump
from Common import data_logger
from Types import resolve

#########################################
#  DHT22 temperature & humidity sensor  #
#########################################
__DHT_OBJ = None
_LOG_NAME = "dht22"


def __init_DHT22():
    global __DHT_OBJ
    if __DHT_OBJ is None:
        from dht import DHT22
        from machine import Pin
        __DHT_OBJ = DHT22(Pin(physical_pin('dhtpin')))
    return __DHT_OBJ


def __temp_hum():
    __init_DHT22().measure()
    temp = __DHT_OBJ.temperature()
    if temp < -273:
        # correction for minus celsius scale
        temp = round(temp/1000, 1)
    return temp, __DHT_OBJ.humidity()


#########################
# Application functions #
#########################

def load():
    """
    Initialize DHT22 hum/temp sensor module
    """
    __init_DHT22()
    return "DHT22 hum/temp sensor module - loaded"

def measure(log=False):
    """
    Measure with dht22
    :return dict: temp, hum
    """
    _temp, _hum = __temp_hum()
    data = {'temp[C]': round(_temp, 2), 'hum[%]': round(_hum, 2)}
    if log:
        data_logger(_LOG_NAME, data=str(data))
    return data


def measure_w_co2(log=False):
    """
    Measure with dht22 and mq135 (CO2)
    :return dict: temp, hum, co2
    """
    from LM_co2 import measure_mq135
    _temp, _hum = __temp_hum()
    data = {'temp[C]': round(_temp, 2), 'hum[%]': round(_hum, 2), 'co2[ppm]': measure_mq135(_temp, _hum)}
    if log:
        data_logger(_LOG_NAME, data=str(data))
    return data


def logger():
    """
    Return temp, hum, (co2) logged data
    """
    data_logger(_LOG_NAME)
    return ''


#######################
# LM helper functions #
#######################

def lmdep():
    """
    Show Load Module dependency
    - List of load modules used by this application
    :return: tuple
    """
    return 'co2'


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_dump('dhtpin')


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('TEXTBOX measure log=False', 'measure_w_co2 log=False',
                             'logger', 'lmdep', 'load', 'pinmap'), widgets=widgets)
