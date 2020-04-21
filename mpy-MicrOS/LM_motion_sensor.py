__PIR_OBJ = None

def __init_PIR_sensor():
    global __PIR_OBJ
    if __PIR_OBJ is None:
        from machine import Pin
        __PIR_OBJ = Pin(10, Pin.IN, Pin.PULL_UP)
    return __PIR_OBJ

def get_PIR_state():
    PIR_OBJ = __init_PIR_sensor()
    return PIR_OBJ.value()

def PIR_deinit():
    global __PIR_OBJ
    PIR_OBJ = __init_PIR_sensor()
    PIR_OBJ.deinit()
    __PIR_OBJ = None
    return "DEINIT PIR SENSOR"

def help():
    return 'get_PIR_state', 'PIR_deinit'
