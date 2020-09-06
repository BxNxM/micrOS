import esp32


def hall():
    # read the internal hall sensor
    return esp32.hall_sensor()


def intemp():
    # read the internal temperature of the MCU, in Farenheit
    return (esp32.raw_temperature() - 32) / 1.8


def touchpin14():
    from machine import TouchPad, Pin
    t = TouchPad(Pin(14))
    return t.read()  # Returns a smaller number when touched


def help():
    return 'hall', 'intemp', 'touchpin14' 'Dedicated functions for esp32.'
