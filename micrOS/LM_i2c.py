__I2C = None


def __init():
    global __I2C
    if __I2C is None:
        from machine import Pin, I2C
        from LogicalPins import get_pin_on_platform_by_key
        __I2C = I2C(-1, Pin(get_pin_on_platform_by_key('i2c_scl')), Pin(get_pin_on_platform_by_key('i2c_sda')))
    return __I2C


def scan():
    # https://docs.micropython.org/en/latest/library/machine.I2C.html
    return __init().scan()


def help():
    return 'scan'
