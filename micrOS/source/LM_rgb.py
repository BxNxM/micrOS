#########################################
#       ANALOG rgb CONTROLLER PARAMS    #
#########################################
from machine import Pin, PWM
from sys import platform
from Common import transition_gen, micro_task
import uasyncio as asyncio
from ConfigHandler import cfgget
from utime import sleep_ms
from LogicalPins import physical_pin, pinmap_dump
from random import randint


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

def __RGB_init():
    if Data.RGB_OBJS[0] is None or Data.RGB_OBJS[1] is None or Data.RGB_OBJS[2] is None:
        red = Pin(physical_pin('redgb'))
        green = Pin(physical_pin('rgreenb'))
        blue = Pin(physical_pin('rgbue'))
        if platform == 'esp8266':
            Data.RGB_OBJS = (PWM(red, freq=1024),
                          PWM(green, freq=1024),
                          PWM(blue, freq=1024))
        else:
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


def load_n_init(cache=None):
    """
    Initiate RGB module
    :param cache bool: file state machine cache: True/False/None(default: automatic True)
    - Load .pds (state machine cache) for this load module
    - Apply loaded states to gpio pins (boot function)
    :return str: Cache state
    """
    from sys import platform
    if cache is None:
        Data.PERSISTENT_CACHE = True if platform == 'esp32' else False
    else:
        Data.PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')     # recover data cache if enabled
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
            Data.RGB_OBJS[1].duty(g_gen.__next__())
            Data.RGB_OBJS[2].duty(b_gen.__next__())
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
                _g = g_gen.__next__()
                _b = b_gen.__next__()
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
                await asyncio.sleep_ms(ms_period)
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
    return pinmap_dump(['redgb', 'rgreenb', 'rgbue'])


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'color r=<0-1000> g=<0-1000> b=<0,1000> smooth=True force=True',\
           'toggle state=None smooth=True', 'load_n_init', \
           'brightness percent=<0-100> smooth=True wake=True',\
           'transition r=None g=None b=None sec=1.0 wake=False',\
           'random smooth=True max_val=1000', 'status', 'subscribe_presence', 'pinmap'
