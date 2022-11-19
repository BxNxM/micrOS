from LM_co2 import measure_mq135
from LogicalPins import physical_pin, pinmap_dump

#########################################
#  DHT22 temperature & humidity sensor  #
#########################################
__DHT_OBJ = None


def __init_DHT11():
    global __DHT_OBJ
    if __DHT_OBJ is None:
        from dht import DHT11
        from machine import Pin
        __DHT_OBJ = DHT11(Pin(physical_pin('dhtpin')))
    return __DHT_OBJ


def __temp_hum():
    __init_DHT11().measure()
    return __DHT_OBJ.temperature(), __DHT_OBJ.humidity()


def measure():
    _temp, _hum = __temp_hum()
    return {'temp [ºC]': _temp, 'hum [%]': _hum}


def measure_w_co2():
    _temp, _hum = __temp_hum()
    return {'temp [ºC]': _temp, 'hum [%]': _hum, 'co2 [ppm]': measure_mq135(_temp, _hum)}


#######################
# LM helper functions #
#######################

def lmdep():
    return 'co2'


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins associated to the module
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_dump('dhtpin')


def help():
    return 'measure', 'measure_w_co2', 'lmdep', 'pinmap'
