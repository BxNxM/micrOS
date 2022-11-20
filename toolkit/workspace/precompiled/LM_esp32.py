import esp32


def hall():
    # read the internal hall sensor
    return esp32.hall_sensor()


def temp():
    # read the internal temperature of the MCU, in Farenheit
    return {'CPU temp [ºC]': '{:.1f}'.format((esp32.raw_temperature() - 32) / 1.8)}


def touch(triglvl=300):
    """
    triglvl - trigger level, value < triglvl decide touched
    """
    from machine import TouchPad, Pin
    from LogicalPins import physical_pin
    t = TouchPad(Pin(physical_pin('touch_0')))
    value = t.read()  # Returns a smaller number when touched
    return {'isTouched': True if value < triglvl else False, 'value': value}


def battery():
    from tinypico import get_battery_voltage, get_battery_charging
    return {'volt': get_battery_voltage(), 'state': get_battery_charging()}


#######################
# LM helper functions #
#######################

def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'hall', 'temp', 'touch', 'battery', 'NOTE: battery only available on tinypico'
