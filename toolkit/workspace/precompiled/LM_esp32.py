import esp32
from Common import syslog

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
    try:
        raw_temp =  esp32.raw_temperature()
    except Exception as e:
        syslog(f"[WARN] cpu temp: {e}")
        return {'CPU temp [C]': -1.0}
    # read the internal temperature of the MCU, in Farenheit
    cpu_temp = round((raw_temp - 32) / 1.8, 1)
    return {'CPU temp [C]': cpu_temp}


def touch(triglvl=300):
    """
    Test function:
    :param triglvl: trigger level, value < triglvl decide touched
    :return dict: verdict isTouched and value
    """
    from machine import TouchPad, Pin
    from microIO import resolve_pin
    t = TouchPad(Pin(resolve_pin('touch_0')))
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

def help(widgets=False):
    """
    [BETA][i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'hall', 'temp', 'touch', 'battery', 'NOTE: battery only available on tinypico'
