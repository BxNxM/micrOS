#########################################
#       ANALOG rgb CONTROLLER PARAMS    #
#########################################
from machine import Pin, PWM
from sys import platform
from Common import transition_gen, micro_task
from utime import sleep_ms
from microIO import bind_pin, pinmap_search
from random import randint
from Types import resolve


class Data:
    """
    Runtime static state machine class
    """
    RGB_OBJS = (None, None, None)
    RGB_CACHE = [197.0, 35.0, 10.0, 0]     # R, G, B (default color) + RGB state (default: off)
    PERSISTENT_CACHE = False
    CH_MAX = 1000                          # maximum value per channel
    TASK_STATE = False
    RGB_TASK_TAG = "rgb._tran"


#########################################
#      ANALOG rgb WITH 3 channel PWM    #
#########################################

def __RGB_init(red_pin=None, green_pin=None, blue_pin=None):
    if Data.RGB_OBJS[0] is None or Data.RGB_OBJS[1] is None or Data.RGB_OBJS[2] is None:
        red = Pin(bind_pin('redgb', red_pin))
        green = Pin(bind_pin('rgreenb', green_pin))
        blue = Pin(bind_pin('rgbue', blue_pin))
        Data.RGB_OBJS = (PWM(red, freq=20480),
                         PWM(green, freq=20480),
                         PWM(blue, freq=20480))
    return Data.RGB_OBJS


def __persistent_cache_manager(mode):
    """
    pds - persistent data structure
    modes:
        r - recover, s - save
    """
    if not Data.PERSISTENT_CACHE:
        return
    if mode == 's':
        # SAVE CACHE
        with open('rgb.pds', 'w') as f:
            f.write(','.join([str(k) for k in Data.RGB_CACHE]))
        return
    try:
        # RESTORE CACHE
        with open('rgb.pds', 'r') as f:
            Data.RGB_CACHE = [float(data) for data in f.read().strip().split(',')]
    except:
        pass


def __state_machine(r, g, b):
    # Save channel duties if LED on
    if r > 0 or g > 0 or b > 0:
        Data.RGB_CACHE = [r, g, b, 1]
    else:
        Data.RGB_CACHE[3] = 0
    # Save state machine (cache)
    __persistent_cache_manager('s')


def load(red_pin=None, green_pin=None, blue_pin=None, cache=True):
    """
    Initiate RGB module
    :param red_pin: optional red color pin to overwrite built-in
    :param green_pin: optional green color pin to overwrite built-in
    :param blue_pin: optional blue color pin to overwrite built-in
    :param cache: file state machine cache: True/False (.pds), default=True
    :return str: Cache state
    """
    Data.PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')     # recover data cache if enabled
    __RGB_init(red_pin, green_pin, blue_pin)
    if Data.RGB_CACHE[3] == 1:
        Data.RGB_CACHE[3] = 0           # Force ON at boot
        toggle(True)
    else:
        color(0, 0, 0, smooth=False)      # If no persistent cache, init all pins low (OFF)
    return "CACHE: {}".format(Data.PERSISTENT_CACHE)


def color(r=None, g=None, b=None, smooth=True, force=True):
    """
    Set RGB values with PWM signal
    :param r int: red value   0-1000
    :param g int: green value 0-1000
    :param b int: blue value  0-1000
    :param smooth bool: enable smooth color transition: True(default)/False
    :param force bool: clean fade generators and set color (default: True)
    :return dict: rgb status - states: R, G, B, S
    """
    def __buttery(r_from, g_from, b_from, r_to, g_to, b_to):
        interval_sec = 0.2
        if Data.RGB_CACHE[3] == 0:
            # Turn from OFF to on (to colors)
            r_from, g_from, b_from = 0, 0, 0
            Data.RGB_CACHE[3] = 1
        rgb_gen, step_ms = transition_gen(r_from, r_to, g_from, g_to, b_from, b_to, interval_sec=interval_sec)
        r_gen = rgb_gen[0]
        g_gen = rgb_gen[1]
        b_gen = rgb_gen[2]
        for _r in r_gen:
            Data.RGB_OBJS[0].duty(_r)
            Data.RGB_OBJS[1].duty(next(g_gen))
            Data.RGB_OBJS[2].duty(next(b_gen))
            sleep_ms(step_ms)

    __RGB_init()
    if force:
        Data.TASK_STATE = False  # STOP TRANSITION TASK, SOFT KILL - USER INPUT PRIO
    # Dynamic input handling: user/cache
    r = Data.RGB_CACHE[0] if r is None else r
    g = Data.RGB_CACHE[1] if g is None else g
    b = Data.RGB_CACHE[2] if b is None else b
    # Set RGB channels
    if smooth:
        __buttery(r_from=Data.RGB_CACHE[0], g_from=Data.RGB_CACHE[1], b_from=Data.RGB_CACHE[2], r_to=r, g_to=g, b_to=b)
    else:
        Data.RGB_OBJS[0].duty(int(r))
        Data.RGB_OBJS[1].duty(int(g))
        Data.RGB_OBJS[2].duty(int(b))
    # Save channels data
    __state_machine(r, g, b)
    return status()


def brightness(percent=None, smooth=True, wake=True):
    """
    Set RGB brightness
    :param percent: int - brightness percentage: 0-100
    :param smooth: bool - enable smooth color transition: True(default)/False
    :param wake: bool - wake up output / if off turn on with new brightness
    :return dict: rgb status - states: R, G, B, S
    """
    # Get color (channel) max brightness
    ch_max = max(Data.RGB_CACHE[:-1])
    # Calculate actual brightness
    actual_percent = ch_max / Data.CH_MAX * 100

    # Return brightness percentage
    if percent is None:
        if Data.RGB_CACHE[3] == 0:
            return "0 %"
        return "{} %".format(actual_percent)
    # Validate input percentage value
    if percent < 0 or percent > 100:
        return "Percent is out of range: 0-100"
    # Percent not changed
    if percent == actual_percent and Data.RGB_CACHE[3] == 1:
        return status()

    # Set brightness percentage
    target_br = Data.CH_MAX * (percent / 100)
    new_rgb = (round(target_br * float(Data.RGB_CACHE[0] / ch_max), 3),
               round(target_br * float(Data.RGB_CACHE[1] / ch_max), 3),
               round(target_br * float(Data.RGB_CACHE[2] / ch_max), 3))
    # Update RGB output
    if Data.RGB_CACHE[3] == 1 or wake:
        return color(new_rgb[0], new_rgb[1], new_rgb[2], smooth=smooth)
    # Update cache only! Data.RGB_CACHE[3] == 0 and wake == False
    Data.RGB_CACHE[0] = new_rgb[0]
    Data.RGB_CACHE[1] = new_rgb[1]
    Data.RGB_CACHE[2] = new_rgb[2]
    return status()


def toggle(state=None, smooth=True):
    """
    Toggle led state based on the stored state
    :param state bool: True(1)/False(0)/None(default - automatic toggle)
    :param smooth bool: enable smooth color transition: True(default)/False
    :return dict: rgb status - states: R, G, B, S
    """
    # Set state directly (inverse) + check change
    if state is not None:
        if bool(state) is bool(Data.RGB_CACHE[3]):
            return status()
        Data.RGB_CACHE[3] = 0 if state else 1

    # Set OFF state (1)
    if Data.RGB_CACHE[3]:
        return color(0, 0, 0, smooth=smooth, force=False)
    # Turn ON with smooth "hack" (0)
    if smooth:
        r, g, b = Data.RGB_CACHE[0], Data.RGB_CACHE[1], Data.RGB_CACHE[2]
        Data.RGB_CACHE[0], Data.RGB_CACHE[1], Data.RGB_CACHE[2] = 0, 0, 0
        return color(r, g, b, smooth=smooth, force=False)
    # Turn ON without smooth (0)
    return color(smooth=smooth, force=False)


def transition(r=None, g=None, b=None, sec=1.0, wake=False):
    """
    [TASK] Set transition color change for long dimming periods < 30sec
    - creates the dimming generators
    :param r: value 0-1000
    :param g: value 0-1000
    :param b: value 0-1000
    :param sec: transition length in sec
    :param wake: bool, wake on setup (auto run on periphery)
    :return: info msg string
    """

    async def _task(ms_period, iterable):
        # [!] ASYNC TASK ADAPTER [*2] with automatic state management
        #   [micro_task->Task] TaskManager access to task internals (out, done attributes)
        with micro_task(tag=Data.RGB_TASK_TAG) as my_task:
            ro, go, bo = __RGB_init()
            r_gen, g_gen, b_gen = iterable[0], iterable[1], iterable[2]
            for _r in r_gen:
                _g = next(g_gen)
                _b = next(b_gen)
                if not Data.TASK_STATE:                         # SOFT KILL TASK - USER INPUT PRIO
                    my_task.out = "Cancelled"
                    return
                if Data.RGB_CACHE[3] == 1 or wake:
                    # Write periphery
                    ro.duty(_r)
                    go.duty(_g)
                    bo.duty(_b)
                # Update periphery cache (value check due to toggle ON value minimum)
                Data.RGB_CACHE[0] = _r if _r > 5 else 5   # SAVE VALUE TO CACHE > 5 ! because toggle
                Data.RGB_CACHE[1] = _g if _g > 5 else 5   # SAVE VALUE TO CACHE > 5 ! because toggle
                Data.RGB_CACHE[2] = _b if _b > 5 else 5   # SAVE VALUE TO CACHE > 5 ! because toggle
                my_task.out = f"Dimming: R:{_r} G:{_g} B:{_b}"
                await my_task.feed(sleep_ms=ms_period)
            if Data.RGB_CACHE[3] == 1 or wake:
                __state_machine(_r, _g, _b)
            my_task.out = f"Dimming DONE: R:{_r} G:{_g} B:{_b}"

    Data.TASK_STATE = True  # Save transition task is stared (kill param to overwrite task with user input)
    # Dynamic input handling: user/cache
    r = Data.RGB_CACHE[0] if r is None else r
    g = Data.RGB_CACHE[1] if g is None else g
    b = Data.RGB_CACHE[2] if b is None else b
    r_from, g_from, b_from = __RGB_init()[0].duty(), __RGB_init()[1].duty(), __RGB_init()[2].duty() # Get current values
    # Create transition generator and calculate step_ms
    rgb_gen, step_ms = transition_gen(r_from, r, g_from, g, b_from, b, interval_sec=sec)
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    state = micro_task(tag=Data.RGB_TASK_TAG, task=_task(ms_period=step_ms, iterable=rgb_gen))
    return "Starting transition" if state else "Transition already running"


def random(smooth=True, max_val=1000):
    """
    Demo function: implements random color change
    :param smooth bool: enable smooth color transition: True(default)/False
    :param max_val: set channel maximum generated value: 0-1000
    :return dict: rgb status - states: R, G, B, S
    """
    r = randint(0, max_val)
    g = randint(0, max_val)
    b = randint(0, max_val)
    return color(r, g, b, smooth=smooth)


def subscribe_presence():
    """
    Initialize LM presence module with ON/OFF callback functions
    :return: None
    """
    from LM_presence import _subscribe
    _subscribe(on=lambda s=True: toggle(s), off=lambda s=False: toggle(s))

#######################
# LM helper functions #
#######################


def status(lmf=None):
    """
    [i] micrOS LM naming convention
    Show Load Module state machine
    :param lmf str: selected load module function aka (function to show state of): None (show all states)
    - micrOS client state synchronization
    :return dict: R, G, B, S
    """
    data = Data.RGB_CACHE
    return {'R': data[0], 'G': data[1], 'B': data[2], 'S': data[3]}


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_search(['redgb', 'rgreenb', 'rgbue'])


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(( 'COLOR color r=<0-1000-10> g b smooth=True force=True',
                              'BUTTON toggle state=<True,False> smooth=True', 'load',
                              'SLIDER brightness percent=<0-100> smooth=True wake=True',
                              'transition r=None g=None b=None sec=1.0 wake=False',
                              'BUTTON random smooth=True max_val=1000',
                              'status', 'subscribe_presence', 'pinmap'), widgets=widgets)
