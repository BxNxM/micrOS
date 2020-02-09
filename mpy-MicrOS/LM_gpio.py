__RLED = None
__GLED = None
__BLED = None

def __RGB_init():
    from machine import Pin, PWM
    global __RLED, __GLED, __BLED
    d7_gpio13_red = Pin(2)
    d4_gpio2_green = Pin(13)
    d3_gpio0_blue = Pin(0)
    __RLED = PWM(d7_gpio13_red, freq=80)
    __GLED = PWM(d4_gpio2_green, freq=80)
    __BLED = PWM(d3_gpio0_blue, freq=80)
    return "RGB pins was inicialized."

def RGB(r=None, g=None, b=None):
    # r, g, b [0 - 1024]
    init_output = ""
    if __RLED is None or __GLED is None or __BLED is None: init_output + __RGB_init() + "\n"
    if r is not None:
        __RLED.duty(r)
    if g is not None:
        __GLED.duty(g)
    if b is not None:
        __BLED.duty(b)
    return init_output + "SET RGB"

def RGB_deinit():
    if __RLED is not None or __GLED is not None or __BLED is not None:
        __RLED.deinit()
        __GLED.deinit()
        __BLED.deinit()
        return "DEINIT RGB"
