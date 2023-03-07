from utime import sleep_ms
from random import randint
import LM_servo as servo
from LM_switch import set_state
from LM_switch import pinmap as pm
from Common import transition, micro_task
import uasyncio as asyncio


class RoboArm:
    CENTER_XY = 77                          # Store XY center servo position 40+(115-40)/2 ~ 77
    ACTUAL_XY = [CENTER_XY, CENTER_XY]      # Set default XY position
    SPEED_MS = 10                           # Set default speed between steps (ms)
    MOVE_RECORD = []                        # Buffer for XY move record/replay
    PLAY_TAG = 'roboarm._play'


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


def load_n_init():
    """
    Initiate roboarm module
    :param cache bool: file state machine cache: True/False/None(default: automatic True)
    - Load .pds (state machine cache) for this load module
    - Apply loaded states to gpio pins (boot function)
    :return str: Cache state
    """
    # Initial positioning
    x, y = RoboArm.CENTER_XY, RoboArm.CENTER_XY
    servo.sduty(x)
    RoboArm.ACTUAL_XY[0] = x
    servo.s2duty(y)
    RoboArm.ACTUAL_XY[1] = y
    # Load move records
    __persistent_cache_manager('r')
    return 'Move to home'


def control(x_new, y_new, speed_ms=None, smooth=True):
    """
    Control robot arm function
    :param x_new: new x position
    :param y_new: new y position
    :param speed_ms: speed - step wait in ms
    :param smooth: smooth transition, default True
    :return str: move verdict
    """
    def __buttery(x_from, y_from, x_to, y_to):
        # Transition effect / smooth position change
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

    # Skip if new XY is the same as current
    if RoboArm.ACTUAL_XY[0] == x_new and RoboArm.ACTUAL_XY[1] == y_new:
        return 'Already on X:{} Y:{}'.format(x_new, y_new)
    # Check input parameter range
    if 40 > x_new > 115 or 40 > y_new > 115:
        return "X{}/Y{} out of range... range: 40-115".format(x_new, y_new)

    # Set arm speed
    RoboArm.SPEED_MS = speed_ms if isinstance(speed_ms, int) else RoboArm.SPEED_MS
    # Get actual position
    x_prev = RoboArm.ACTUAL_XY[0]
    y_prev = RoboArm.ACTUAL_XY[1]

    if smooth:
        # Move roboarm to position
        __buttery(x_prev, y_prev, x_new, y_new)
        RoboArm.ACTUAL_XY = [x_new, y_new]
    else:
        # Fast move robaorm to position
        if x_new is not None:
            servo.sduty(x_new)
            RoboArm.ACTUAL_XY[0] = x_new
        if y_new is not None:
            servo.s2duty(y_new)
            RoboArm.ACTUAL_XY[1] = y_new
    return 'Move X{}->{} Y{}->{}'.format(x_prev, RoboArm.ACTUAL_XY[0], y_prev, RoboArm.ACTUAL_XY[1])


def boot_move(speed_ms=None):
    """
    Full range demo move
    :param speed_ms: speed - step wait in ms
    :return: verdict
    """
    RoboArm.SPEED_MS = speed_ms if isinstance(speed_ms, int) else RoboArm.SPEED_MS
    # Set arm to center
    load_n_init()
    sleep_ms(RoboArm.SPEED_MS*2)
    # Test X
    control(40, RoboArm.CENTER_XY)
    control(115, RoboArm.CENTER_XY)
    control(RoboArm.CENTER_XY, RoboArm.CENTER_XY)
    sleep_ms(RoboArm.SPEED_MS*2)
    # Test Y
    control(RoboArm.CENTER_XY, 40)
    control(RoboArm.CENTER_XY, 115)
    control(RoboArm.CENTER_XY, RoboArm.CENTER_XY)
    sleep_ms(RoboArm.SPEED_MS*2)
    # Test multiple
    control(40, 40)     # left top
    control(115, 115)    # right bottom
    control(115, 40)    # right top
    control(40, 115)     # left bottom
    sleep_ms(RoboArm.SPEED_MS*2)
    # Enter to home
    control(RoboArm.CENTER_XY, RoboArm.CENTER_XY)     # Move home
    servo.deinit()
    return 'Boot move'


def standby():
    """
    Standby roboarm - OFF switch
    """
    set_state(False)
    control(RoboArm.CENTER_XY, 45)
    servo.deinit()
    return 'Standby mode'


def jiggle():
    """
    Joggle roboarm in small range
    """
    x, y = RoboArm.ACTUAL_XY
    for _ in range(5):
        jx = randint(-2, 2)
        jy = randint(-2, 2)
        control(x+jx, y+jy)
        sleep_ms(RoboArm.SPEED_MS)
    control(x, y)
    return 'JJiggle :)'


async def _play(args, deinit, delay):
    """
    :param args: X Y X2 Y2
    """
    # ASYNC TASK ADAPTER [*2] with automatic state management
    #   [micro_task->Task] TaskManager access to task internals (out, done attributes)
    with micro_task(tag=RoboArm.PLAY_TAG) as task:
        # ON LASER
        set_state(True)
        for i in range(0, len(args), 2):
            # Make servo control
            x, y = args[i], args[i+1]
            control(x, y)
            # Update task output buffer
            if task is not None:
                task.out = "Roboarm X:{} Y:{}".format(x, y)
            # Async wait between steps
            await asyncio.sleep_ms(delay)
        if deinit:
            servo.deinit()
        # OFF LASER
        set_state(False)


def play(*args, s=None, delay=None, deinit=True):
    """
    [TASK] Runs move instructions from input or RoboArm.MOVE_RECORD
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

    # Start play - servo XY in async task
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    state = micro_task(tag=RoboArm.PLAY_TAG, task=_play(args, deinit, delay))
    if state:
        return 'Play: {} steps'.format(int(len(args)/2))
    return 'Play - already running'


def record(clean=False, rec_limit=8):
    """
    Record function for move automation :D
    - Store actual X, Y
    :param clean: clean move cache (True), default: False
    :param rec_limit: record x,y data set limit (default: 10)
    :return: verdict
    """
    if clean:
        RoboArm.MOVE_RECORD = []
        __persistent_cache_manager('s')
        return 'Record was cleaned'
    coord_len = int(len(RoboArm.MOVE_RECORD)/2)
    if coord_len < rec_limit:
        x, y = RoboArm.ACTUAL_XY
        RoboArm.MOVE_RECORD.append(x)
        RoboArm.MOVE_RECORD.append(y)
        __persistent_cache_manager('s')
        return f'Record[{coord_len}]: X:{x} Y:{y}'
    return f'Record[{coord_len}]: limit exceeded: {rec_limit}'


def random(x_range=20, y_range=20, speed_ms=5):
    """
    Move to random position
    :param x_range: +/- x(35) from center
    :param y_range: +/- y(35) from center
    :return str: move verdict
    """
    center_x = RoboArm.CENTER_XY
    center_y = RoboArm.CENTER_XY
    to_x = randint(center_x-x_range, center_x+x_range)
    to_y = randint(center_y-y_range, center_y+y_range)
    return control(x_new=to_x, y_new=to_y, speed_ms=speed_ms, smooth=True)


#######################
# LM helper functions #
#######################

def status(lmf=None):
    """
    [i] micrOS LM naming convention
    Show Load Module state machine
    :param lmf str: selected load module function aka (function to show state of): None (show all states)
    - micrOS client state synchronization
    :return dict: X, Y
    """
    # Roboarm - Joystick dedicated widget input - [OK]
    return {'X': RoboArm.ACTUAL_XY[0], 'Y': RoboArm.ACTUAL_XY[1]}


def lmdep():
    """
    Show Load Module dependency
    - List of load modules used by this application
    :return: tuple
    """
    return 'servo', 'switch'


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    s_pm = servo.pinmap()
    s_pm.update({'switch_1': pm()['switch_1']})
    return s_pm


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'control x=<40-115> y=<40-115> s=<ms delay> smooth=True', 'boot_move', 'standby',\
           'jiggle', 'play 40 40 115 115 s=<speed ms> delay=<ms> deinit=True',\
           'record clean=False', 'random x_range=20 y_range=20 speed_ms=5',\
           'load_n_init', 'pinmap', 'status', 'lmdep'
