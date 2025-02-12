from neopixel import NeoPixel
from machine import Pin
from sys import platform
from utime import sleep_ms
from Common import transition_gen, micro_task
from microIO import bind_pin, pinmap_search
from random import randint
from Types import resolve


#########################################
#       DIGITAL CONTROLLER PARAMS       #
#########################################
class Data:
    # Values: R, G, B, STATE_ON_OFF, IS_INITIALIZED
    DCACHE = [100, 100, 100, 0]
    CH_MAX = 255
    NEOPIXEL_OBJ = None
    PERSISTENT_CACHE = False
    RGB_TASK_TAG = "neopixel._tran"
    TASK_STATE = False


#########################################
#        DIGITAL rgb WITH 1 "PWM"       #
#########################################


def __init_NEOPIXEL(pin=None, n=24):
    """
    Init NeoPixel module
    n - number of led fragments
    """
    if Data.NEOPIXEL_OBJ is None:
        neopixel_pin = Pin(bind_pin('neop', number=pin))         # Get Neopixel pin from LED PIN pool
        Data.NEOPIXEL_OBJ = NeoPixel(neopixel_pin, n)                 # initialize for max 8 segments
        del neopixel_pin
    return Data.NEOPIXEL_OBJ


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
        with open('neopixel.pds', 'w') as f:
            f.write(','.join([str(k) for k in Data.DCACHE]))
        return
    try:
        # RESTORE CACHE
        with open('neopixel.pds', 'r') as f:
            Data.DCACHE = [float(data) for data in f.read().strip().split(',')]
    except:
        pass


def __state_machine(r, g, b):
    # Set cache
    if r > 0 or g > 0 or b > 0:
        Data.DCACHE = [r, g, b, 1]                         # Cache colors + state (True-ON)
    else:
        Data.DCACHE[3] = 0                                 # State - False - OFF
    __persistent_cache_manager('s')                        # Save cache - Data.DCACHE -  to file


#########################################
#             USER FUNCTIONS            #
#########################################

def load(ledcnt=24, pin=None, cache=True):
    """
    Initiate NeoPixel RGB module
    :param ledcnt: number of led segments
    :param pin: optional number to overwrite default pin
    :param cache: default True, store stages on disk +  Load (.pds)
    :return str: Cache state
    """
    Data.PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')         # recover data cache
    _ledcnt = __init_NEOPIXEL(pin=pin, n=ledcnt).n
    if Data.PERSISTENT_CACHE and Data.DCACHE[3] == 1:
        Data.DCACHE[3] = 0                  # Force ON at boot
        toggle(True)
    return "CACHE: {}, LED CNT: {}".format(Data.PERSISTENT_CACHE, _ledcnt)


def color(r=None, g=None, b=None, smooth=True, force=True):
    """
    Set NEOPIXEL RGB values
    :param r: red value   0-255
    :param g: green value 0-255
    :param b: blue value  0-255
    :param smooth: runs colors change with smooth effect
    :param force: clean fade generators and set color
    :return dict: rgb status - states: R, G, B, S
    """

    def __buttery(r_from, g_from, b_from, r_to, g_to, b_to):
        interval_sec = 0.2
        if Data.DCACHE[3] == 0:
            # Turn from OFF to on (to colors)
            r_from, g_from, b_from = 0, 0, 0
            Data.DCACHE[3] = 1
        rgb_gen_obj, step_ms = transition_gen(r_from, r_to, g_from, g_to, b_from, b_to, interval_sec=interval_sec)
        r_gen = rgb_gen_obj[0]
        g_gen = rgb_gen_obj[1]
        b_gen = rgb_gen_obj[2]
        for _r in r_gen:
            _g = next(g_gen)
            _b = next(b_gen)
            for lcnt in range(0, __init_NEOPIXEL().n):
                Data.NEOPIXEL_OBJ[lcnt] = (_r, _g, _b)
            Data.NEOPIXEL_OBJ.write()
            sleep_ms(step_ms)
    if force:
        Data.TASK_STATE = False  # STOP TRANSITION TASK, SOFT KILL - USER INPUT PRIO

    r = Data.DCACHE[0] if r is None else r
    g = Data.DCACHE[1] if g is None else g
    b = Data.DCACHE[2] if b is None else b
    # Set each LED for the same color
    if smooth:
        __buttery(r_from=Data.DCACHE[0], g_from=Data.DCACHE[1], b_from=Data.DCACHE[2], r_to=r, g_to=g, b_to=b)
    else:
        for element in range(0, __init_NEOPIXEL().n):          # Iterate over led string elements
            Data.NEOPIXEL_OBJ[element] = (r, g, b)             # Set LED element color
        Data.NEOPIXEL_OBJ.write()                              # Send data to device
    # Set cache
    __state_machine(r, g, b)
    return status()


def brightness(percent=None, smooth=True, wake=True):
    """
    Set neopixel brightness
    :param percent: (int) brightness percentage: 0-100
    :param smooth: (bool) enable smooth color transition: True(default)/False
    :param wake: bool - wake up output / if off turn on with new brightness
    :return dict: rgb status - states: R, G, B, S
    """
    # Get color (channel) max brightness
    ch_max = max(Data.DCACHE[:-1])
    # Calculate actual brightness
    actual_percent = ch_max / Data.CH_MAX * 100

    # Return brightness percentage
    if percent is None:
        if Data.DCACHE[3] == 0:
            return "0 %"
        return "{} %".format(actual_percent)
    # Validate input percentage value
    if percent < 0 or percent > 100:
        return "Percent is out of range: 0-100"
    # Percent not changed
    if percent == actual_percent and Data.DCACHE[3] == 1:
        return status()

    # Set brightness percentage
    target_br = Data.CH_MAX * (percent / 100)
    new_rgb = (target_br * float(Data.DCACHE[0] / ch_max),
               target_br * float(Data.DCACHE[1] / ch_max),
               target_br * float(Data.DCACHE[2]) / ch_max)
    # Update RGB output
    if Data.DCACHE[3] == 1 or wake:
        return color(round(new_rgb[0], 3), round(new_rgb[1], 3), round(new_rgb[2], 3), smooth=smooth)
    # Update cache only! Data.DCACHE[3] == 0 and wake == False
    Data.DCACHE[0] = int(new_rgb[0])
    Data.DCACHE[1] = int(new_rgb[1])
    Data.DCACHE[2] = int(new_rgb[2])
    return status()


def segment(r=None, g=None, b=None, s=0, cache=False, write=True):
    """
    Set single segment by index on neopixel
    :param r: red value 0-255
    :param g: green value 0-255
    :param b: blue value 0-255
    :param s: segment - index 0-ledcnt
    :param cache: cache color (update .pds file)
    :param write: send color buffer to neopixel (update LEDs)
    :return dict: rgb status - states: R, G, B, S
    """
    r = Data.DCACHE[0] if r is None else r
    g = Data.DCACHE[1] if g is None else g
    b = Data.DCACHE[2] if b is None else b
    neo_n = __init_NEOPIXEL().n
    if s <= neo_n:
        Data.NEOPIXEL_OBJ[s] = (r, g, b)
        # Send colors to neopixel
        if write:
            Data.NEOPIXEL_OBJ.write()
        # Cache handling
        if cache:
            if r > 0 or g > 0 or b > 0:
                Data.DCACHE = [r, g, b, 1]
            else:
                Data.DCACHE[3] = 0
            __persistent_cache_manager('s')  # Save cache - Data.DCACHE -  to file

        return status()
    return "NEOPIXEL index error: {} > {}".format(s, neo_n)


def toggle(state=None, smooth=True):
    """
    Toggle led state based on the stored state
    :param state: True(1)/False(0)
    :param smooth: runs colors change with smooth effect
    :return dict: rgb status - states: R, G, B, S
    """
    # Set state directly (inverse) + check change
    if state is not None:
        if bool(state) is bool(Data.DCACHE[3]):
            return status()
        Data.DCACHE[3] = 0 if state else 1

    # Set OFF state (1)
    if Data.DCACHE[3] == 1:
        return color(r=0, g=0, b=0, smooth=smooth, force=False)
    # Turn ON with smooth "hack" (0)
    if smooth:
        r, g, b = Data.DCACHE[0], Data.DCACHE[1], Data.DCACHE[2]
        Data.DCACHE[0], Data.DCACHE[1], Data.DCACHE[2] = 0, 0, 0
        return color(r, g, b, smooth=smooth, force=False)
    # Turn ON without smooth (0)
    return color(smooth=smooth, force=False)


def transition(r=None, g=None, b=None, sec=1.0, wake=False):
    """
    [TASK] Set transition color change for long dimming periods < 30sec
    - creates the dimming generators
    :param r: red channel 0-255
    :param g: green channel 0-255
    :param b: blue channel 0-255
    :param sec: transition length in sec
    :param wake: bool, wake on setup (auto run on periphery)
    :return: info msg string
    """

    async def _task(ms_period, iterable):
        # [!] ASYNC TASK ADAPTER [*2] with automatic state management
        #   [micro_task->Task] TaskManager access to task internals (out, done attributes)
        r_gen, g_gen, b_gen = iterable[0], iterable[1], iterable[2]
        with micro_task(tag=Data.RGB_TASK_TAG) as my_task:
            for r_val in r_gen:
                if not Data.TASK_STATE:
                    my_task.out = "Cancelled"
                    return
                g_val = next(g_gen)
                b_val = next(b_gen)
                if Data.DCACHE[3] == 1 or wake:
                    # Write periphery
                    for element in range(0, __init_NEOPIXEL().n):           # Iterate over led string elements
                        Data.NEOPIXEL_OBJ[element] = (r_val, g_val, b_val)  # Set LED element color
                    Data.NEOPIXEL_OBJ.write()                               # Send data to device
                # Update periphery cache (value check due to toggle ON value minimum)
                Data.DCACHE[0] = r_val if r_val > 5 else 5   # SAVE VALUE TO CACHE > 5 ! because toggle
                Data.DCACHE[1] = g_val if g_val > 5 else 5   # SAVE VALUE TO CACHE > 5 ! because toggle
                Data.DCACHE[2] = b_val if b_val > 5 else 5   # SAVE VALUE TO CACHE > 5 ! because toggle
                my_task.out = f"Dimming: R:{r_val} G:{g_val} B:{b_val}"
                await my_task.feed(sleep_ms=ms_period)
            if Data.DCACHE[3] == 1 or wake:
                __state_machine(r=r_val, g=g_val, b=b_val)
            my_task.out = f"Dimming DONE: R:{r_val} G:{g_val} B:{b_val}"

    Data.TASK_STATE = True      # Save transition task is stared (kill param to overwrite task with user input)
    r_from, g_from, b_from = Data.DCACHE[0], Data.DCACHE[1], Data.DCACHE[2]
    r_to = Data.DCACHE[0] if r is None else r
    g_to = Data.DCACHE[1] if g is None else g
    b_to = Data.DCACHE[2] if b is None else b
    # Create transition generator and calculate step_ms
    rgb_gen, step_ms = transition_gen(r_from, r_to, g_from, g_to, b_from, b_to, interval_sec=sec)
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    state = micro_task(tag=Data.RGB_TASK_TAG, task=_task(ms_period=step_ms, iterable=rgb_gen))
    return "Starting transition" if state else "Transition already running"


def random(smooth=True, max_val=255):
    """
    Demo function: implements random color change
    :param smooth: (bool) enable smooth color transition: True(default)/False
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
    # Neopixel(=RGB) dedicated widget input - [OK]
    data = Data.DCACHE
    return {'R': data[0], 'G': data[1], 'B': data[2], 'S': data[3]}


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_search('neop')


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('COLOR color r=<0-255-5> g b smooth=True force=True',
                             'BUTTON toggle state=<True,False> smooth=True',
                             'load ledcnt=24',
                             'SLIDER brightness percent=<0-100> smooth=True wake=True',
                             'segment r g b s=<0-n>',
                             'transition r g b sec=1.0 wake=False',
                             'BUTTON random smooth=True max_val=254',
                             'status',
                             'subscribe_presence',
                             'pinmap',
                             'help widgets=False'), widgets=widgets)
