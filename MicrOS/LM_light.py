__RLED = None
__GLED = None
__BLED = None
__RGB_STATE = False
__RGB_CACHE = ()

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
    global __RGB_STATE
    __RGB_init()
    _rgb_state = False
    if r is not None:
        __RLED.duty(r)
        _rgb_state = _rgb_state or (True if r > 0 else False)
    if g is not None:
        __GLED.duty(g)
        _rgb_state = _rgb_state or (True if g > 0 else False)
    if b is not None:
        __BLED.duty(b)
        _rgb_state = _rgb_state or (True if b > 0 else False)
    __RGB_STATE = _rgb_state
    return "SET RGB"

def RGB_deinit():
    from time import sleep
    global __RLED, __GLED, __BLED, __RGB_STATE
    RGB(0,0,0)
    __RGB_STATE = False
    sleep(0.5)
    __RLED.deinit()
    __GLED.deinit()
    __BLED.deinit()
    __RLED = None
    __GLED = None
    __BLED = None
    return "DEINIT RGB"

def RGB_toggle():
    global __RGB_STATE, __RGB_CACHE
    if __RGB_STATE:
        __RGB_STATE = False
        __RGB_CACHE = (__RLED.duty(), __GLED.duty(), __GLED.duty())
        RGB(0, 0, 0)
    else:
        __RGB_STATE = True
        if len(__RGB_CACHE) != 3:
            RGB(800, 800, 800)
        else:
            RGB(__RGB_CACHE[0], __RGB_CACHE[1], __RGB_CACHE[2])
    return "ON" if __RGB_STATE else "OFF"

def help():
    return ('RGB', 'RGB_toggle', 'RGB_deinit')
