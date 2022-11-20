import machine, onewire, ds18x20, time
from LogicalPins import physical_pin, pinmap_dump

DS_OBJ = None


def __init_DS18():
    global DS_OBJ
    if DS_OBJ is None:
        ds_pin = machine.Pin(physical_pin('ds18'))
        DS_OBJ = ds18x20.DS18X20(onewire.OneWire(ds_pin))
    return DS_OBJ


#########################
# Application functions #
#########################

def measure():
    """
    Measure with digital onewire temperature sensor
    - ds18
    :return str: temp string
    """
    data = []
    # Init DS18
    ds_obj = __init_DS18()
    # Search devices
    roms = ds_obj.scan()
    if len(roms) == 0:
        return 'Sensor(s) was not found.'
    # Convert value to temp
    ds_obj.convert_temp()
    time.sleep_ms(750)
    # Get temp data by device id (rom)
    for rom in roms:
        data.append(ds_obj.read_temp(rom))
    # Return with single data
    if len(data) == 1:
        return {'temp [ºC]': data[0]}
    # Return with multiple data
    return data


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
    return pinmap_dump('ds18')


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'measure', 'pinmap'
