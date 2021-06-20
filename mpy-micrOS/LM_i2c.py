__I2C = None


def __init():
    global __I2C
    if __I2C is None:
        from machine import Pin, I2C
        from LogicalPins import physical_pin
        __I2C = I2C(-1, Pin(physical_pin('i2c_scl')), Pin(physical_pin('i2c_sda')))
    return __I2C


def scan():
    # https://docs.micropython.org/en/latest/library/machine.I2C.html
    return __init().scan()


#######################
# LM helper functions #
#######################

def help():
    return 'scan'
