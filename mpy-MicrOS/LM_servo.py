__SERVO = None

def __SERVO_init():
    global __SERVO
    if __SERVO is None:
        from machine import Pin, PWM
        from LogicalPins import getPlatformValByKey
        try:
            pin = Pin(getPlatformValByKey('servo'))
            __SERVO = PWM(pin,freq=50)
            del pin
        except Exception as e:
            return str(e)
    return __SERVO


def Servo(duty=100):
    s = __SERVO_init()
    if duty > 120:
        duty = 120
    elif duty < 40:
        duty = 40
    try:
        # duty for servo is between 40 - 115
        s.duty(duty)
        return "SET SERVO: duty: {}".format(duty)
    except Exception as e:
        return str(e)

def Servo_demo():
    from time import sleep
    Servo(40)
    sleep(1)
    Servo(120)
    sleep(1)
    Servo(70)
    return "Servo DEMO"

def Servo_deinit():
    s = __SERVO_init()
    try:
        s.deinit()
        return "DEINIT SERVO"
    except Exception as e:
        return str(e)


def help():
    return ('Servo(duty=<int>40-115)', 'Servo_demo', 'Servo_deinit')
