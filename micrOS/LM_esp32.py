import esp32


def hall():
    # read the internal hall sensor
    return esp32.hall_sensor()


def temp():
    # read the internal temperature of the MCU, in Farenheit
    return (esp32.raw_temperature() - 32) / 1.8


def touch(triglvl=300):
    """
    triglvl - trigger level, value < triglvl decide touched
    """
    from machine import TouchPad, Pin
    from LogicalPins import get_pin_on_platform_by_key
    t = TouchPad(Pin(get_pin_on_platform_by_key('touch_0')))
    value = t.read()  # Returns a smaller number when touched
    return {'isTouched': True if value < triglvl else False, 'value': value}


def battery():
    from tinypico import get_battery_voltage, get_battery_charging
    return {'volt': get_battery_voltage(), 'state': get_battery_charging()}


def help():
    return 'hall', 'temp', 'touch' 'Dedicated functions for esp32.', 'battery', 'NOTE: only available on tinypico'
