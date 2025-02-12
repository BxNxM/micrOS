from microIO import bind_pin, pinmap_search

__I2C = None


def __init():
    global __I2C
    if __I2C is None:
        from machine import Pin, I2C
        __I2C = I2C(-1, Pin(bind_pin('i2c_scl')), Pin(bind_pin('i2c_sda')))
    return __I2C


def scan():
    """
    I2C scan function - experimental
    :return list: list of devices
    """
    devices = [ hex(device) for device in  __init().scan() ]
    return devices


def discover():
    """
    Discover devices
    """
    known_addresses = {hex(0x0A): "trackball", hex(0x3c): "oled",
                       hex(0x76): "bme280", hex(0x10): 'veml7700'}
    devices = scan()
    output = {"unknown": []}
    for k in devices:
        if k in known_addresses:
            device_name = known_addresses[k]
            output[device_name] = k
        else:
            output["unknown"].append(k)
    return output

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
    return pinmap_search(['i2c_scl', 'i2c_sda'])


def help(widgets=False):
    """
    [BETA][i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'scan', 'discover', 'pinmap'
