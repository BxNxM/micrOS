
PIR_OBJ = None

def __init_PIR_sensor():
    global PIR_OBJ
    if PIR_OBJ is None:
        from machine import Pin
        PIR_OBJ = Pin(10, Pin.IN, Pin.PULL_UP)
    return PIR_OBJ

def get_PIR_state():
    PIR_OBJ = __init_PIR_sensor()
    return PIR_OBJ.value()
