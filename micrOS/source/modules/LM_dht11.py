from microIO import bind_pin, pinmap_search
from Common import data_logger
from Types import resolve

#########################################
#  DHT22 temperature & humidity sensor  #
#########################################
__DHT_OBJ = None
_LOG_NAME = "dht11"


def __init_DHT11():
    global __DHT_OBJ
    if __DHT_OBJ is None:
        from dht import DHT11
        from machine import Pin
        __DHT_OBJ = DHT11(Pin(bind_pin('dhtpin')))
    return __DHT_OBJ


def __temp_hum():
    __init_DHT11().measure()
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
    Initialize DHT11 hum/temp sensor module
    """
    __init_DHT11()
    return "DHT11 hum/temp sensor module - loaded"

def measure(log=False):
    """
    Measure with dht11
    :return dict: temp, hum
    """
    _temp, _hum = __temp_hum()
    data = {'temp[C]': round(_temp, 2), 'hum[%]': round(_hum, 2)}
    if log:
        data_logger(_LOG_NAME, data=str(data))
    return data

def logger():
    """
    Return temp, hum logged data
    """
    data_logger(_LOG_NAME)
    return ''


#######################
# LM helper functions #
#######################

def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_search('dhtpin')


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('TEXTBOX measure log=False',
                             'logger', 'load', 'pinmap'), widgets=widgets)
