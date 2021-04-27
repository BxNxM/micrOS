import LM_servo as servo
from time import sleep_ms


class RoboArm:
    ACTUAL_XY = [75, 75]
    SPEED_MS = 5

    @staticmethod
    def __get_gcb(a, b):
        """ Get greatest common divider """
        gcd = 1
        for i in range(1, min(a, b) + 1):
            if a % i == 0 and b % i == 0:
                gcd = i
        return gcd

    @staticmethod
    def get_gcb(a, b):
        gcd = RoboArm.__get_gcb(a, b)
        if gcd <= 1:
            gcd = RoboArm.__get_gcb(a+1, b)
        if gcd <= 1:
            gcd = RoboArm.__get_gcb(a+1, b-1)
        # Return parallel step calculation + double for better resolution
        return gcd * 2


def control(x_new, y_new, s=None):
    # Skip if X;Y is the same
    if RoboArm.ACTUAL_XY[0] == x_new and RoboArm.ACTUAL_XY[1] == y_new:
        return 'Already was moved X:{} Y:{}'.format(x_new, y_new)
    # Set arm speed
    RoboArm.SPEED_MS = s if isinstance(s, int) else RoboArm.SPEED_MS
    # Get actual position
    x_prev = RoboArm.ACTUAL_XY[0]
    y_prev = RoboArm.ACTUAL_XY[1]
    # Get difference between positions
    x_diff = x_new - x_prev
    y_diff = y_new - y_prev
    # Move X and Y servo parallel, threshold: 5
    if abs(x_diff) > 5 and abs(y_diff) > 5:
        gcd = RoboArm.get_gcb(abs(x_diff), abs(y_diff))
        x_step = round(x_diff / gcd)
        y_step = round(y_diff / gcd)
        for k in range(1, gcd+1):
            servo.sduty(x_prev + k*x_step)
            servo.s2duty(y_prev + k*y_step)
            sleep_ms(RoboArm.SPEED_MS*2)
    else:
        # Move X servo only
        if abs(x_diff) > 0:
            xpm = -1 if x_diff < 1 else 1
            for k in range(1, abs(x_diff)+1):
                servo.sduty(x_prev + (k*xpm))
                sleep_ms(RoboArm.SPEED_MS)
        # Move Y servo only
        if abs(y_diff) > 0:
            ypm = -1 if y_diff < 1 else 1
            for k in range(1, abs(y_diff)+1):
                servo.s2duty(y_prev + (k*ypm))
                sleep_ms(RoboArm.SPEED_MS)
    # Set exact position
    servo.sduty(x_prev+x_diff)
    servo.s2duty(y_prev+y_diff)
    RoboArm.ACTUAL_XY = [x_prev+x_diff, y_prev+y_diff]
    return 'Move X{}->{} Y{}->{}'.format(x_prev, RoboArm.ACTUAL_XY[0], y_prev, RoboArm.ACTUAL_XY[1])


def rawcontrol(x=None, y=None):
    # x - 40-115
    # y - 40-115
    if x is not None:
        servo.sduty(x)
        RoboArm.ACTUAL_XY[0] = x
    if y is not None:
        servo.s2duty(y)
        RoboArm.ACTUAL_XY[1] = y
    return 'Move arm X:{} y:{}'.format(x, y)


def boot_move(s=None):
    RoboArm.SPEED_MS = s if isinstance(s, int) else RoboArm.SPEED_MS
    # Set arm to center
    load_n_init()
    sleep_ms(RoboArm.SPEED_MS*2)
    # Test X move (Y=65)
    control(40, 65)
    control(115, 65)
    control(75, 65)
    sleep_ms(RoboArm.SPEED_MS*2)
    # Test Y move (X=75)
    control(75, 40)
    control(75, 96)
    control(75, 65)
    sleep_ms(RoboArm.SPEED_MS*2)
    # Test multiple
    control(40, 40)     # left top
    control(115, 96)    # right bottom - ISSUE
    control(115, 40)    # right top
    control(40, 96)     # left bottom - ISSUE
    sleep_ms(RoboArm.SPEED_MS*2)
    # Enter to home
    control(75, 65)     # Move home - ISSUE
    return 'Boot move done'


def load_n_init(x=75, y=65):
    servo.sduty(x)
    RoboArm.ACTUAL_XY[0] = x
    servo.s2duty(y)
    RoboArm.ACTUAL_XY[1] = y
    return 'Set to zero position done'


#######################
# LM helper functions #
#######################

def lmdep():
    return 'LM_servo'


def help():
    return 'control x=<40-115> y=<40-115>, s=<ms delay>', 'rawcontrol x=<40-115> y=<40-115>',\
           'boot_move', 'load_n_init', 'lmdep'
