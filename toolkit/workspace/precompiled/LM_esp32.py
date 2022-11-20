import esp32

#########################
# Application functions #
#########################


def hall():
    """
    Measure with esp32 built-in hall sensor
    """
    # read the internal hall sensor
    return esp32.hall_sensor()


def temp():
    """
    Measure CPU temperature
    """
    # read the internal temperature of the MCU, in Farenheit
    return {'CPU temp [ºC]': '{:.1f}'.format((esp32.raw_temperature() - 32) / 1.8)}


def touch(triglvl=300):
    """
    Test function:
    :param triglvl: trigger level, value < triglvl decide touched
    :return dict: verdict isTouched and value
    """
    from machine import TouchPad, Pin
    from LogicalPins import physical_pin
    t = TouchPad(Pin(physical_pin('touch_0')))
    value = t.read()  # Returns a smaller number when touched
    return {'isTouched': True if value < triglvl else False, 'value': value}


def battery():
    """
    TinyPico battery manager interface
    :return dict: volt, state (is charging)
    """
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
