def __RGB_init():
    from machine import Pin, PWM
    from LogicalPins import getPlatformValByKey
    d7_gpio13_red = Pin(getPlatformValByKey('pwm_red'))
    d4_gpio2_green = Pin(getPlatformValByKey('pwm_green'))
    d3_gpio0_blue = Pin(getPlatformValByKey('pwm_blue'))
    __RLED = PWM(d7_gpio13_red, freq=80)
    __GLED = PWM(d4_gpio2_green, freq=80)
    __BLED = PWM(d3_gpio0_blue, freq=80)
    return __RLED, __GLED, __BLED

def RGB(r=None, g=None, b=None, __RLED=None, __GLED=None, __BLED=None):
    if __RLED is None or __GLED is None or __BLED is None:
        __RLED, __GLED, __BLED = __RGB_init()
    if r is not None:
        __RLED.duty(r)
    if g is not None:
        __GLED.duty(g)
    if b is not None:
        __BLED.duty(b)
    return "SET RGB"

def RGB_deinit(__RLED=None, __GLED=None, __BLED=None):
    if __RLED is None or __GLED is None or __BLED is None:
        __RLED, __GLED, __BLED = __RGB_init()
    RGB(r=0, g=0, b=0, __RLED=__RLED, __GLED=__GLED, __BLED=__BLED)
    __RLED.deinit()
    __GLED.deinit()
    __BLED.deinit()
    return "DEINIT RGB"

def Servo(duty=100):
    from machine import Pin, PWM
    from LogicalPins import getPlatformValByKey
    if duty > 120:
        duty = 120
    elif duty < 40:
        duty = 40
    try:
        pin = Pin(getPlatformValByKey('servo'))
        servo = PWM(pin,freq=50)
        # duty for servo is between 40 - 115
        servo.duty(duty)
        return "SET SERVO: duty: {}".format(duty)
    except Exception as e:
        return str(e)

def Servo_deinit():
    from machine import Pin, PWM
    from LogicalPins import getPlatformValByKey
    try:
        pin = Pin(getPlatformValByKey('servo'))
        servo = PWM(pin,freq=50)
        servo.deinit()
        del pin
        return "DEINIT SERVO"
    except Exception as e:
        return str(e)
