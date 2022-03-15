from utime import sleep_ms
from random import randint
import LM_servo as servo
from LM_switch import set_state
from Common import transition


class RoboArm:
    ACTUAL_XY = [75, 70]
    SPEED_MS = 10
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


def control(x_new, y_new, s=None, smooth=True):
    def __buttery(x_from, y_from, x_to, y_to):
        x_diff = abs(x_from-x_to)
        y_diff = abs(y_from-y_to)
        max_diff = y_diff if x_diff < y_diff else x_diff
        step_ms = RoboArm.SPEED_MS                                  # resolution
        interval_sec = float(RoboArm.SPEED_MS * 0.001 * max_diff)   # calculate travel time in sec
        x = transition(from_val=x_from, to_val=x_to, step_ms=step_ms, interval_sec=interval_sec)
        y = transition(from_val=y_from, to_val=y_to, step_ms=step_ms, interval_sec=interval_sec)
        for _x in x:
            servo.sduty(_x)
            servo.s2duty(y.__next__())
            sleep_ms(step_ms)

    # Skip if X;Y is the same
    if RoboArm.ACTUAL_XY[0] == x_new and RoboArm.ACTUAL_XY[1] == y_new:
        return 'Already was moved X:{} Y:{}'.format(x_new, y_new)

    # Set arm speed
    RoboArm.SPEED_MS = s if isinstance(s, int) else RoboArm.SPEED_MS
    # Get actual position
    x_prev = RoboArm.ACTUAL_XY[0]
    y_prev = RoboArm.ACTUAL_XY[1]

    if smooth:
        __buttery(x_prev, y_prev, x_new, y_new)
        RoboArm.ACTUAL_XY = [x_new, y_new]
    else:
        if x_new is not None:
            servo.sduty(x_new)
            RoboArm.ACTUAL_XY[0] = x_new
        if y_new is not None:
            servo.s2duty(y_new)
            RoboArm.ACTUAL_XY[1] = y_new
    return 'Move X{}->{} Y{}->{}'.format(x_prev, RoboArm.ACTUAL_XY[0], y_prev, RoboArm.ACTUAL_XY[1])


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
    servo.deinit()
    return 'Boot move'


def standby():
    set_state(False)
    control(75, 45)
    servo.deinit()
    return 'Standby mode'


def jiggle():
    x, y = RoboArm.ACTUAL_XY
    for _ in range(5):
        jx = randint(-1, 1)
        jy = randint(-1, 1)
        control(x+jx, y+jy)
        sleep_ms(RoboArm.SPEED_MS)
    control(x, y)
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
    return 'servo', 'switch'


def help():
    return 'control x=<40-115> y=<40-115> s=<ms delay> smooth=True', 'boot_move', 'standby',\
           'jiggle', 'play 40 40 115 115 s=<ms> delay=<ms>, deinit=True',\
           'record clean=False', 'load_n_init', 'status', 'lmdep'
