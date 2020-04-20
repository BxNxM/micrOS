DHT_OBJ = None


def __init_DHT22():
    global DHT_OBJ
    if DHT_OBJ is None:
        from dht import DHT22
        from machine import Pin
        from LogicalPins import getPlatformValByKey
        DHT_OBJ = DHT22(Pin(getPlatformValByKey('dht_pin')))
    return DHT_OBJ


def temp():
    __init_DHT22().measure()
    return "{} ºC".format(DHT_OBJ.temperature())


def humidity():
    __init_DHT22().measure()
    return "{} %".format(DHT_OBJ.humidity())


def help():
    return ('temp', 'humidity')

