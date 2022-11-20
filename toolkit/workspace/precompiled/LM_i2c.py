from LogicalPins import physical_pin, pinmap_dump

__I2C = None


def __init():
    global __I2C
    if __I2C is None:
        from machine import Pin, I2C
        __I2C = I2C(-1, Pin(physical_pin('i2c_scl')), Pin(physical_pin('i2c_sda')))
    return __I2C


def scan():
    """
    I2C scan function - experimental
    :return list: list of devices
    """
    # https://docs.micropython.org/en/latest/library/machine.I2C.html
    return __init().scan()


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
    return pinmap_dump(['i2c_scl', 'i2c_sda'])


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'scan', 'pinmap'
