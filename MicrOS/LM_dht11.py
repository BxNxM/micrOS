from LM_co2 import measure_mq135

#########################################
#  DHT22 temperature & humidity sensor  #
#########################################
__DHT_OBJ = None


def __init_DHT11():
    global __DHT_OBJ
    if __DHT_OBJ is None:
        from dht import DHT11
        from machine import Pin
        from LogicalPins import get_pin_on_platform_by_key
        __DHT_OBJ = DHT11(Pin(get_pin_on_platform_by_key('simple_1')))
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


def help():
    return 'measure', 'measure_w_co2'

