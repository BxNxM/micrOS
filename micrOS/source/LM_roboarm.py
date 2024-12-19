from utime import sleep_ms
from random import randint
import LM_servo as servo
from LM_switch import set_state, pinmap as switch_pinmap
from Common import transition, micro_task
from Types import resolve


class RoboArm:
    CENTER_XY = 77                          # Store XY center servo position 40+(115-40)/2 ~ 77
    RANGE = (40, 115)                       # Save servo duty range (normally 0-180 degree)
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


def load():
    """
    Initiate roboarm module
    - move servo motors to middle position
    """
    # Initial positioning
    x, y = RoboArm.CENTER_XY, RoboArm.CENTER_XY
    servo.sduty(x)
    RoboArm.ACTUAL_XY[0] = x
    servo.s2duty(y)
    RoboArm.ACTUAL_XY[1] = y
    # Load move records
    __persistent_cache_manager('r')
    return f'Init and Move to home X{x}, Y{y}'


def control(x, y, speed_ms=None, smooth=True):
    """
    Control robot arm function
    :param x: new x position (40-115)
    :param y: new y position (40-115)
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
            servo.s2duty(next(y))
            sleep_ms(step_ms)

    # Skip if new XY is the same as current
    if RoboArm.ACTUAL_XY[0] == x and RoboArm.ACTUAL_XY[1] == y:
        return f"Already on X:{x} Y:{y}"
    # Check input parameter range
    if RoboArm.RANGE[0] > x > RoboArm.RANGE[1] or RoboArm.RANGE[0] > y > RoboArm.RANGE[1]:
        return f"X{x}/Y{y} out of range... range: {RoboArm.RANGE[0]}-{RoboArm.RANGE[1]}"

    # Set arm speed
    RoboArm.SPEED_MS = speed_ms if isinstance(speed_ms, int) else RoboArm.SPEED_MS
    # Get actual position
    x_prev = RoboArm.ACTUAL_XY[0]
    y_prev = RoboArm.ACTUAL_XY[1]

    if smooth:
        # Move roboarm to position
        __buttery(x_prev, y_prev, x, y)
        RoboArm.ACTUAL_XY = [x, y]
    else:
        # Fast move robaorm to position
        servo.sduty(x)
        servo.s2duty(y)
        RoboArm.ACTUAL_XY[0] = x
        RoboArm.ACTUAL_XY[1] = y
    return 'Move X{}->{} Y{}->{}'.format(x_prev, RoboArm.ACTUAL_XY[0], y_prev, RoboArm.ACTUAL_XY[1])


def boot_move(speed_ms=None):
    """
    Full range demo move
    :param speed_ms: speed - step wait in ms
    :return: verdict
    """
    RoboArm.SPEED_MS = speed_ms if isinstance(speed_ms, int) else RoboArm.SPEED_MS
    # Set arm to center
    load()
    sleep_ms(RoboArm.SPEED_MS*2)
    # Test X
    control(RoboArm.RANGE[0], RoboArm.CENTER_XY)
    control(RoboArm.RANGE[1], RoboArm.CENTER_XY)
    control(RoboArm.CENTER_XY, RoboArm.CENTER_XY)
    sleep_ms(RoboArm.SPEED_MS*2)
    # Test Y
    control(RoboArm.CENTER_XY, RoboArm.RANGE[0])
    control(RoboArm.CENTER_XY, RoboArm.RANGE[1])
    control(RoboArm.CENTER_XY, RoboArm.CENTER_XY)
    sleep_ms(RoboArm.SPEED_MS*2)
    # Test multiple
    control(RoboArm.RANGE[0], RoboArm.RANGE[0])     # left top
    control(RoboArm.RANGE[1], RoboArm.RANGE[1])    # right bottom
    control(RoboArm.RANGE[1], RoboArm.RANGE[0])    # right top
    control(RoboArm.RANGE[0], RoboArm.RANGE[1])     # left bottom
    sleep_ms(RoboArm.SPEED_MS*2)
    # Enter to home
    control(RoboArm.CENTER_XY, RoboArm.CENTER_XY)     # Move home
    sleep_ms(RoboArm.SPEED_MS)
    # Enter to calibration laser holder mode
    control(RoboArm.CENTER_XY, RoboArm.RANGE[1])      # Move to X (middle) and Y (most down) for holder positioning.

    servo.deinit()
    return 'Boot sequence: init + end ranges + laser positioning'


def standby(y_pos=45):
    """
    Standby roboarm - OFF laser switch
    """
    set_state(False)
    control(RoboArm.CENTER_XY, y_pos)
    servo.deinit()
    return 'Standby mode'


def jiggle(delta=2):
    """
    Joggle roboarm in small range
    :param delta: jiggle delta from current position (full range: 40-115)
    """
    x, y = RoboArm.ACTUAL_XY
    for _ in range(5):
        jx = randint(-delta, delta)
        jy = randint(-delta, delta)
        control(x+jx, y+jy)
        sleep_ms(RoboArm.SPEED_MS)
    control(x, y)
    return f'JJiggle: {delta} :)'


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
            await task.feed(sleep_ms=delay)
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


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    s_pm = servo.pinmap()
    s_pm.update(switch_pinmap())
    return s_pm


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('JOYSTICK control x=<40-115> y=<40-115> speed_ms=5 smooth=True',
                             'BUTTON boot_move speed_ms=10',
                             'BUTTON standby y_pos=45',
                             'BUTTON jiggle delta=3',
                             'play 40 40 115 115 s=<speed ms> delay=<ms> deinit=True',
                             'BUTTON play deinit=True',
                             'record clean=False rec_limit=8',
                             'random x_range=20 y_range=20 speed_ms=5',
                             'load', 'pinmap',
                             'status'), widgets=widgets)
