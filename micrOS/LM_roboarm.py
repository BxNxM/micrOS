from time import sleep_ms
import LM_servo as servo
from LM_switch import set_state


class RoboArm:
    ACTUAL_XY = [75, 70]
    SPEED_MS = 5


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
    # Absolut x, y diff
    x_abs = abs(x_diff)
    y_abs = abs(y_diff)
    # Move X and Y servo parallel, threshold: 2
    if x_abs > 0 and y_abs > 0:
        # x, y vector direction
        x_dir = -1 if x_diff < 0 else 1
        y_dir = -1 if y_diff < 0 else 1
        if x_abs <= y_abs:
            y_step = float(y_abs) / x_abs
            for x in range(1, x_abs+1):
                servo.sduty(x_prev + x*x_dir)
                servo.s2duty(y_prev + round(x*y_step)*y_dir)
                sleep_ms(RoboArm.SPEED_MS)
        else:
            x_step = float(x_abs) / y_abs
            for y in range(1, y_abs+1):
                servo.sduty(x_prev + round(y*x_step)*x_dir)
                servo.s2duty(y_prev + y*y_dir)
                sleep_ms(RoboArm.SPEED_MS)
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
    return 'Move (raw) X:{} y:{}'.format(x, y)


def boot_move(s=None):
    RoboArm.SPEED_MS = s if isinstance(s, int) else RoboArm.SPEED_MS
    # Set arm to center
    load_n_init()
    sleep_ms(RoboArm.SPEED_MS*2)
    # Test X move (Y=65)
    control(40, 70)
    control(115, 70)
    control(75, 70)
    sleep_ms(RoboArm.SPEED_MS*2)
    # Test Y move (X=75)
    control(75, 40)
    control(75, 115)
    control(75, 70)
    sleep_ms(RoboArm.SPEED_MS*2)
    # Test multiple
    control(40, 40)     # left top
    control(115, 115)    # right bottom
    control(115, 40)    # right top
    control(40, 115)     # left bottom
    sleep_ms(RoboArm.SPEED_MS*2)
    # Enter to home
    control(75, 70)     # Move home
    return 'Boot move'


def standby():
    set_state(False)
    servo.sduty(75)
    RoboArm.ACTUAL_XY[0] = 75
    servo.s2duty(45)
    RoboArm.ACTUAL_XY[1] = 45
    sleep_ms(200)
    servo.deinit()
    return 'Standby mode'


def load_n_init(x=75, y=70):
    servo.sduty(x)
    RoboArm.ACTUAL_XY[0] = x
    servo.s2duty(y)
    RoboArm.ACTUAL_XY[1] = y
    return 'Move to home'


#######################
# LM helper functions #
#######################

def lmdep():
    return 'LM_servo', 'LM_switch'


def help():
    return 'control x=<40-115> y=<40-115>, s=<ms delay>', 'rawcontrol x=<40-115> y=<40-115>',\
           'boot_move', 'load_n_init', 'standby', 'lmdep'
