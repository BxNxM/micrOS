__RLED = None
__GLED = None
__BLED = None

def __RGB_init():
    from machine import Pin, PWM
    from LogicalPins import getPlatformValByKey
    global __RLED, __GLED, __BLED
    d7_gpio13_red = Pin(getPlatformValByKey('pwm_red'))
    d4_gpio2_green = Pin(getPlatformValByKey('pwm_green'))
    d3_gpio0_blue = Pin(getPlatformValByKey('pwm_blue'))
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
    init_output = ""
    if __RLED is None or __GLED is None or __BLED is None: init_output + __RGB_init() + "\n"
    RGB(0,0,0)
    __RLED.deinit()
    __GLED.deinit()
    __BLED.deinit()
    return init_output + "DEINIT RGB"

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
