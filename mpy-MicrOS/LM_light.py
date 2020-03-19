__RLED = None
__GLED = None
__BLED = None

def __RGB_init():
    global __RLED, __GLED, __BLED
    if __RLED is None or __GLED is None or __BLED is None:
        from machine import Pin, PWM
        from LogicalPins import getPlatformValByKey
        d7_gpio13_red = Pin(getPlatformValByKey('pwm_red'))
        d4_gpio2_green = Pin(getPlatformValByKey('pwm_green'))
        d3_gpio0_blue = Pin(getPlatformValByKey('pwm_blue'))
        __RLED = PWM(d7_gpio13_red, freq=80)
        __GLED = PWM(d4_gpio2_green, freq=80)
        __BLED = PWM(d3_gpio0_blue, freq=80)

def RGB(r=None, g=None, b=None):
    __RGB_init()
    if r is not None:
        __RLED.duty(r)
    if g is not None:
        __GLED.duty(g)
    if b is not None:
        __BLED.duty(b)
    return "SET RGB"

def RGB_deinit():
    __RGB_init()
    RGB(r=0, g=0, b=0)
    __RLED.deinit()
    __GLED.deinit()
    __BLED.deinit()
    return "DEINIT RGB"
