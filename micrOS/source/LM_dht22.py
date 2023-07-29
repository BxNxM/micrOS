from LogicalPins import physical_pin, pinmap_dump
from Common import data_logger

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
    return __DHT_OBJ.temperature(), __DHT_OBJ.humidity()


#########################
# Application functions #
#########################

def measure(log=False):
    """
    Measure with dht22
    :return dict: temp, hum
    """
    _temp, _hum = __temp_hum()
    data = {'temp [ºC]': round(_temp, 2), 'hum [%]': round(_hum, 2)}
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
    data = {'temp [ºC]': round(_temp, 2), 'hum [%]': round(_hum, 2), 'co2 [ppm]': measure_mq135(_temp, _hum)}
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


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'measure log=False', 'measure_w_co2 log=False', 'logger', 'lmdep', 'pinmap'
