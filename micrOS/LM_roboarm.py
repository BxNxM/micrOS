import LM_servo as servo
from time import sleep_ms

__ACTUAL_XY = (75, 75)
__SPEED_MS = 5


def control(x_new, y_new, s=None):
    global __ACTUAL_XY, __SPEED_MS

    def get_gcb(a, b):
        i = 1
        gcd = 1
        while i <= a and i <= b:
            if a % i == 0 and b % i == 0:
                gcd = i
            i = i + 1
        return gcd
    __SPEED_MS = s if isinstance(s, int) else __SPEED_MS
    x_prev = __ACTUAL_XY[0]
    y_prev = __ACTUAL_XY[1]
    x_diff = x_new - x_prev
    y_diff = y_new - y_prev
    gcd = get_gcb(abs(x_diff), abs(y_diff))
    x_step = round(x_diff / gcd)
    y_step = round(y_diff / gcd)
    for k in range(1, gcd+1):
        servo.sduty(x_prev + k*x_step)
        servo.s2duty(y_prev + k*y_step)
        sleep_ms(__SPEED_MS)
    __ACTUAL_XY = (x_prev+x_diff, y_prev+y_diff)
    return 'Move X{}->{} Y{}->{}'.format(x_prev, __ACTUAL_XY[0], y_prev, __ACTUAL_XY[1])


def rawcontrol(x=None, y=None):
    # x - 40-115
    # y - 40-115
    if x is not None:
        servo.sduty(x)
    if y is not None:
        servo.s2duty(y)
    return 'Move arm X:{} y:{}'.format(x, y)


def boot_move(s=None):
    global __SPEED_MS
    __SPEED_MS = s if isinstance(s, int) else __SPEED_MS
    # Set arm to center
    load_n_init()
    # Test X move
    for x in range(75, 40, -1):
        servo.sduty(x)
        sleep_ms(__SPEED_MS)
    for x in range(40, 115):
        servo.sduty(x)
        sleep_ms(__SPEED_MS)
    for x in range(115, 75, -1):
        servo.sduty(x)
        sleep_ms(__SPEED_MS)
    # Test Y move
    for y in range(75, 40, -1):
        servo.s2duty(y)
        sleep_ms(__SPEED_MS)
    for y in range(40, 96):
        servo.s2duty(y)
        sleep_ms(__SPEED_MS)
    for y in range(96, 75, -1):
        servo.s2duty(y)
        sleep_ms(__SPEED_MS)
    return 'Boot move done'


def load_n_init():
    servo.sduty(75)
    sleep_ms(__SPEED_MS)
    servo.s2duty(75)
    sleep_ms(__SPEED_MS)
    return 'Set to zero position done'


#######################
# LM helper functions #
#######################

def lmdep():
    return 'LM_servo'


def help():
    return 'control x=<40-115> y=<40-115>, s=<ms delay>', 'rawcontrol x=<40-115> y=<40-115>',\
           'boot_move', 'load_n_init', 'lmdep'
