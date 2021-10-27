from utime import sleep_ms
from random import randint
import LM_servo as servo
from LM_switch import set_state


class RoboArm:
    ACTUAL_XY = [75, 70]
    SPEED_MS = 5
    MOVE_RECORD = []


def __persistent_cache_manager(mode):
    """
    pds - persistent data structure
    modes:
        r - recover, s - save
    """

    if mode == 's':
        # SAVE CACHE
        with open('rarm.pds', 'w') as f:
            f.write(','.join([str(k) for k in RoboArm.MOVE_RECORD]))
        return
    try:
        # RESTORE CACHE
        with open('rarm.pds', 'r') as f:
            RoboArm.MOVE_RECORD = [int(data) for data in f.read().strip().split(',')]
    except:
        pass


def load_n_init(x=75, y=70):
    servo.sduty(x)
    RoboArm.ACTUAL_XY[0] = x
    servo.s2duty(y)
    RoboArm.ACTUAL_XY[1] = y
    __persistent_cache_manager('r')
    return 'Move to home'


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


def jiggle():
    x, y = RoboArm.ACTUAL_XY
    for _ in range(5):
        jx = randint(-1, 1)
        jy = randint(-1, 1)
        servo.sduty(x+jx)
        servo.s2duty(y+jy)
        sleep_ms(RoboArm.SPEED_MS)
    servo.sduty(x)
    servo.s2duty(y)
    return 'JJiggle :)'


def play(*args, s=None, delay=None, deinit=True):
    """
    Runs move instructions from input or RoboArm.MOVE_RECORD
    :param args: X Y X2 Y2 ...
    :param s: SPEED_MS (delay)
    :param delay: delay in ms between steps
    :param deinit: deinit servo after execution
    :return: verdict
    """
    RoboArm.SPEED_MS = s if isinstance(s, int) else RoboArm.SPEED_MS
    delay = delay if isinstance(delay, int) else 10
    # Parse args as a list
    args = list(args)
    # Execute MOVE_RECORD if no input was provided
    args = RoboArm.MOVE_RECORD if len(args) < 2 else args
    set_state(True)
    for i in range(0, len(args), 2):
        x, y = args[i], args[i+1]
        control(x, y)
        sleep_ms(delay)
    if deinit:
        servo.deinit()
    set_state(False)
    return 'MovePipe: {} move was played.'.format(int(len(args)/2))


def record(clean=False):
    """
    Record function for move automation :D
    - Store actual X, Y
    :return: verdict
    """
    if clean:
        RoboArm.MOVE_RECORD = []
        __persistent_cache_manager('s')
        return 'Record was cleaned'
    x, y = RoboArm.ACTUAL_XY
    RoboArm.MOVE_RECORD.append(x)
    RoboArm.MOVE_RECORD.append(y)
    __persistent_cache_manager('s')
    return 'Record[{}]: X:{} Y:{}'.format(int(len(RoboArm.MOVE_RECORD)/2), x, y)


#######################
# LM helper functions #
#######################

def status(lmf=None):
    # Roboarm - Joystick dedicated widget input - [OK]
    return {'X': RoboArm.ACTUAL_XY[0], 'Y': RoboArm.ACTUAL_XY[1]}


def lmdep():
    return 'LM_servo', 'LM_switch'


def help():
    return 'control x=<40-115> y=<40-115>, s=<ms delay>', 'rawcontrol x=<40-115> y=<40-115>',\
           'boot_move', 'standby', 'jiggle', 'play 40 40 115 115 s=<ms> delay=<ms>, deinit=True',\
           'record clean=False', 'load_n_init', 'status', 'lmdep'
