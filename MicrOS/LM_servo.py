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

def Servo(duty=100):
    __SERVO_init()
    if duty > 120:
        duty = 120
    elif duty < 40:
        duty = 40
    try:
        # duty for servo is between 40 - 115
        __SERVO.duty(duty)
        return "SET SERVO: duty: {}".format(duty)
    except Exception as e:
        return str(e)

def Servo_deinit():
    __SERVO_init()
    try:
        __SERVO.deinit()
        return "DEINIT SERVO"
    except Exception as e:
        return str(e)

def help():
    return ('Servo(duty=<int>40-120)', 'Servo_deinit')
