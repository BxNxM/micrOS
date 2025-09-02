from machine import Pin, PWM
from microIO import bind_pin, pinmap_search


# Cache of last set motor speeds (motor1, motor2) to ensure state() reports the latest values
# even if hardware PWM duty readout is delayed or unsupported on some boards
__MOTOR_SPEEDS = [0, 0] # motor1, motor2
__L298N_OBJS = []

PWM_FREQ = 50
# Deprecated LM_L298N_DCmotor: l298speed, l298dir_1, l298dir_2
PIN_BINDINGS = [
    ('l298n_ENA', 10), ('l298n_INA', 12), ('l298n_INB', 11),  # motor 1
    ('l298n_ENB', 3),  ('l298n_INC', 9),  ('l298n_IND', 40),  # motor 2
]
STATE_MAP = {
    (1, 0): 'forward',
    (0, 1): 'backward',
    (0, 0): 'coast',
    (1, 1): 'brake'
}


def __l298n_init():
    global __L298N_OBJS
    if not __L298N_OBJS:
        for index, (name, pin) in enumerate(PIN_BINDINGS):
            if index % 3 == 0: # PWM pin
                pwm = PWM(bind_pin(name, pin), freq=PWM_FREQ)
                pwm.duty(0)
                __L298N_OBJS.append(pwm)
            else:
                p = Pin(bind_pin(name, pin), Pin.OUT)
                p.value(0)
                __L298N_OBJS.append(p)
    return __L298N_OBJS


def __get_motor_state(motor_index):
    objlist = __l298n_init()
    pwm_index = motor_index * 3
    in1, in2 = objlist[pwm_index + 1].value(), objlist[pwm_index + 2].value()
    state = STATE_MAP.get((in1, in2), 'unknown')
    return {'speed': __MOTOR_SPEEDS[motor_index], 'state': state}


#########################
# Application functions #
#########################

def load(pwm_freq:int=None):
    """
    [i] micrOS LM naming convention
    Load the L298N motor driver module
    """
    global PWM_FREQ
    if pwm_freq is not None:
        PWM_FREQ = pwm_freq
    __l298n_init()
    return "Motor driver loaded successfully."


def state(motor=0):
    """
    [i] micrOS LM naming convention
    Get the current state of a motor or all motors
    :param motor: Motor number (1 or 2) or None for all motors
    """
    if motor == 1:
        return {'motor1': __get_motor_state(0)}
    elif motor == 2:
        return {'motor2': __get_motor_state(1)}
    else:
        return {
            'motor1': __get_motor_state(0),
            'motor2': __get_motor_state(1)
        }


def _control_motor(motor, in1, in2):
    objlist = __l298n_init()
    motor_index = 0 if motor == 1 else 3
    objlist[motor_index + 1].value(in1)
    objlist[motor_index + 2].value(in2)


def speed(motor, speed:int=1023):
    """
    Set the speed of a motor
    :param motor: Motor number (1 or 2)
    :param speed: Speed value (0-1023)
    :return: Current motor state
    """
    if not (0 <= speed <= 1023):
        return {'speed': 'value range error'}
    pwm_index = 0 if motor == 1 else 3
    motor_index = 0 if motor == 1 else 1
    __l298n_init()[pwm_index].duty(speed)
    __MOTOR_SPEEDS[motor_index] = speed
    return state(motor)


def direction(motor, forward: bool=True):
    """
    Set the direction of a motor
    :param motor: Motor number (1 or 2)
    :param forward: True if motor should move forward, False if backward
    :return: Current motor state
    """
    _control_motor(motor, 1 if forward else 0, 0 if forward else 1)
    return state(motor)


def coast(motor):
    """
    Coast the motor
    :param motor: Motor number (1 or 2)
    """
    _control_motor(motor, 0, 0)
    return state(motor)


def brake(motor):
    """
    Brake the motor
    :param motor: Motor number (1 or 2)
    :return: Current motor state
    """
    _control_motor(motor, 1, 1)
    return state(motor)


#######################
# LM helper functions #
#######################

def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_search([name for name, _ in PIN_BINDINGS])


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return (
        'speed motor=<1/2> speed=<0-1023>', 
        'direction motor=<1/2> forward=<True/False>',
        'coast motor=<1/2>',
        'brake motor=<1/2>',
        'state motor=<0/1/2>',
        'pinmap'
    )