from machine import ADC

def temp():
    """
    Measure CPU temperature - raspberry pi pico w (rp2)
    """
    sensor_temp = ADC(4)
    conversion_factor = 3.3 / 65535
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706) / 0.001721
    return {'CPU temp [C]': temperature}


def help(widgets=False):
    """
    [BETA]
    """
    return 'temp'