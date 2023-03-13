#########################################
#       ANALOG CCT CONTROLLER PARAMS    #
#########################################
from machine import Pin, PWM
from sys import platform
from utime import sleep_ms
from Common import transition_gen, micro_task
import uasyncio as asyncio
from ConfigHandler import cfgget
from LogicalPins import physical_pin, pinmap_dump
from random import randint


class Data:
    CWWW_OBJS = (None, None)
    CWWW_CACHE = [500, 500, 0]           # cold white / warm white / state
    CH_MAX = 1000
    PERSISTENT_CACHE = False
    CCT_TASK_TAG = 'cct._tran'
    HUE_TASK_TAG = 'cct._hue'
    TASK_STATE = False


#########################################
#      ANALOG CCT WITH 2 channel PWM    #
#########################################

def __cwww_init():
    if Data.CWWW_OBJS[0] is None or Data.CWWW_OBJS[1] is None:
        cw = Pin(physical_pin('cwhite'))
        ww = Pin(physical_pin('wwhite'))
        if platform == 'esp8266':
            Data.CWWW_OBJS = (PWM(cw, freq=1024),
                              PWM(ww, freq=1024))
        else:
            Data.CWWW_OBJS = (PWM(cw, freq=20480),
                              PWM(ww, freq=20480))
    return Data.CWWW_OBJS


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
        with open('cwww.pds', 'w') as f:
            f.write(','.join([str(k) for k in Data.CWWW_CACHE]))
        return
    try:
        # RESTORE CACHE
        with open('cwww.pds', 'r') as f:
            Data.CWWW_CACHE = [float(data) for data in f.read().strip().split(',')]
    except:
        pass


def __state_machine(c, w):
    # Cache channel duties if ON
    if c > 0 or w > 0:
        Data.CWWW_CACHE = [Data.CWWW_OBJS[0].duty(), Data.CWWW_OBJS[1].duty(), 1]
    else:
        Data.CWWW_CACHE[2] = 0
    # Save config
    __persistent_cache_manager('s')


#########################
# Application functions #
#########################

def load_n_init(cache=None):
    """
    Initiate Cold white / Warm white LED module
    :param cache bool: file state machine cache: True/False/None(default: automatic True)
    - Load .pds (state machine cache) for this load module
    - Apply loaded states to gpio pins (boot function)
    :return str: Cache state
    """
    from sys import platform
    if cache is None:
        Data.PERSISTENT_CACHE = False if platform == 'esp8266' else True
    else:
        Data.PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')        # recover data cache
    if Data.CWWW_CACHE[2] == 1:
        Data.CWWW_CACHE[2] = 0             # Force ON at boot
        toggle(True)
    else:
        white(0, 0, smooth=False)          # Init pins at bootup
    return "CACHE: {}".format(Data.PERSISTENT_CACHE)


def white(cw=None, ww=None, smooth=True, force=True):
    """
    Set CCT values with PWM signal
    :param cw: cold white value   0-1000
    :param ww: warm white value 0-1000
    :param smooth: (bool) runs white channels change with smooth effect
    :param force: (bool) clean fade generators and set color
    :return dict: cct status - states: CW, WW, S
    """
    def __buttery(ww_from, cw_from, ww_to, cw_to):
        interval_sec = 0.2
        if Data.CWWW_CACHE[2] == 0:
            # Turn from OFF to on (to whites)
            ww_from, cw_from = 0, 0
            Data.CWWW_CACHE[2] = 1
        gen_list, step_ms = transition_gen(ww_from, ww_to, cw_from, cw_to, interval_sec=interval_sec)
        ww_gen = gen_list[0]
        cw_gen = gen_list[1]
        for _ww in ww_gen:
            Data.CWWW_OBJS[1].duty(_ww)
            Data.CWWW_OBJS[0].duty(cw_gen.__next__())
            sleep_ms(step_ms)

    if force:
        Data.TASK_STATE = False  # STOP TRANSITION TASK, SOFT KILL - USER INPUT PRIO
    __cwww_init()
    cw = Data.CWWW_CACHE[0] if cw is None else cw
    ww = Data.CWWW_CACHE[1] if ww is None else ww
    if smooth:
        __buttery(ww_from=Data.CWWW_CACHE[1], cw_from=Data.CWWW_CACHE[0], ww_to=ww, cw_to=cw)
    else:
        Data.CWWW_OBJS[0].duty(cw)
        Data.CWWW_OBJS[1].duty(ww)
    __state_machine(c=cw, w=ww)
    return status()


def brightness(percent=None, smooth=True, wake=True):
    """
    Set CCT brightness
    :param percent: int - brightness percentage: 0-100
    :param smooth: bool - enable smooth color transition: True(default)/False
    :param wake: bool - wake up output / if off turn on with new brightness
    :return dict: cct status - states: CW, WW, S
    """
    # Get color (channel) max brightness
    ch_max = max(Data.CWWW_CACHE[:-1])
    # Calculate actual brightness
    actual_percent = ch_max / Data.CH_MAX * 100

    # Return brightness percentage
    if percent is None:
        if Data.CWWW_CACHE[2] == 0:
            return "0 %"
        return "{} %".format(actual_percent)
    # Validate input percentage value
    if percent < 0 or percent > 100:
        return "Percent is out of range: 0-100"
    # Percent not changed
    if percent == actual_percent and Data.CWWW_CACHE[2] == 1:
        return status()

    # Set brightness percentage
    target_br = Data.CH_MAX * (percent / 100)
    new_cct = (int(target_br * float(Data.CWWW_CACHE[0] / ch_max)),
               int(target_br * float(Data.CWWW_CACHE[1] / ch_max)))
    # Handle background HUE task update
    hue_task = micro_task(Data.HUE_TASK_TAG)
    if hue_task is not None and not hue_task.done:
        return white(new_cct[0], new_cct[1], smooth=False, force=False)
    # Forced (default) output write + cancel task in background
    if Data.CWWW_CACHE[2] == 1 or wake:
        return white(new_cct[0], new_cct[1], smooth=smooth)
    # Update cache only! Data.CWWW_CACHE[2] == 0 and wake == False
    Data.CWWW_CACHE[0] = new_cct[0]
    Data.CWWW_CACHE[1] = new_cct[1]
    return status()


def toggle(state=None, smooth=True):
    """
    Toggle led state based on the stored state
    :param state bool: True(1)/False(0)/None(default - automatic toggle)
    :param smooth bool: enable smooth color transition: True(default)/False
    :return dict: cct status - states: CW, WW, S
    """
    # Set state directly (inverse) + check change
    if state is not None:
        if bool(state) is bool(Data.CWWW_CACHE[2]):
            return status()
        Data.CWWW_CACHE[2] = 0 if state else 1

    # Set OFF state (1)
    if Data.CWWW_CACHE[2]:
        return white(0, 0, smooth=smooth, force=False)
    # Turn ON with smooth "hack" (0)
    if smooth:
        cw, ww = Data.CWWW_CACHE[0], Data.CWWW_CACHE[1]
        Data.CWWW_CACHE[0], Data.CWWW_CACHE[1] = 0, 0
        return white(cw, ww, smooth=smooth, force=False)
    # Turn ON without smooth (0)
    return white(smooth=smooth, force=False)


def transition(cw=None, ww=None, sec=1.0, wake=False):
    """
    [TASK] Set transition color change for long dimming periods < 30sec
    - creates the dimming generators
    :param cw: cold white 0-1000
    :param ww: warm white 0-1000
    :param sec: transition length in sec
    :param wake: bool, wake on setup (auto run on periphery)
    :return: info msg string
    """

    async def _task(ms_period, iterable):
        # [!] ASYNC TASK ADAPTER [*2] with automatic state management
        #   [micro_task->Task] TaskManager access to task internals (out, done attributes)
        cw_obj, ww_obj = __cwww_init()[0], __cwww_init()[1]
        cw_gen, ww_gen = iterable[0], iterable[1]
        with micro_task(tag=Data.CCT_TASK_TAG) as my_task:
            for cw_val in cw_gen:
                if not Data.TASK_STATE:                         # SOFT KILL TASK - USER INPUT PRIO
                    my_task.out = "Cancelled"
                    return
                ww_val = ww_gen.__next__()
                if Data.CWWW_CACHE[2] == 1 or wake:
                    # Write periphery
                    cw_obj.duty(cw_val)
                    ww_obj.duty(ww_val)
                # Update periphery cache (value check due to toggle ON value minimum)
                Data.CWWW_CACHE[0] = cw_val if cw_val > 5 else 5   # SAVE VALUE TO CACHE > 5 ! because toggle
                Data.CWWW_CACHE[1] = ww_val if ww_val > 5 else 5   # SAVE VALUE TO CACHE > 5 ! because toggle
                my_task.out = f"Dimming: CW:{cw_val} WW:{ww_val}"
                await asyncio.sleep_ms(ms_period)
            if Data.CWWW_CACHE[2] == 1 or wake:
                __state_machine(c=cw_val, w=ww_val)
            my_task.out = f"Dimming DONE: CW:{cw_val} WW:{ww_val}"

    Data.TASK_STATE = True      # Save transition task is stared (kill param to overwrite task with user input)
    cw_from, ww_from = __cwww_init()[0].duty(), __cwww_init()[1].duty()
    cw_to = Data.CWWW_CACHE[0] if cw is None else cw
    ww_to = Data.CWWW_CACHE[1] if ww is None else ww
    # Create transition generator and calculate step_ms
    cct_gen, step_ms = transition_gen(cw_from, cw_to, ww_from, ww_to, interval_sec=sec)
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    state = micro_task(tag=Data.CCT_TASK_TAG, task=_task(ms_period=step_ms, iterable=cct_gen))
    return "Starting transition" if state else "Transition already running"


def hue_transition(percent, sec=1.0, wake=False):
    """
    [TASK] Set HUE transition independently from brightness
    - Running warm and cold white ratio change
    - USE cct brightness function to set brightness besides this transition (running)
    :param percent: warm channel ratio in percent 0-100
    :param sec: transition length
    :param wake: bool, wake on setup (auto run on periphery)
    :return: info msg string
    """

    async def _task(ms_period, iterable):
        cw_obj, ww_obj = __cwww_init()[0], __cwww_init()[1]
        with micro_task(tag=Data.HUE_TASK_TAG) as my_task:
            for hue_precent in iterable:
                if not Data.TASK_STATE:                         # SOFT KILL TASK - USER INPUT PRIO
                    my_task.out = "Cancelled"
                    return
                # Set brightness percentage
                target_cold = 1000 - hue_precent
                #print("CW: {}% WW: {}%".format(target_cold, hue_precent))
                all_ch_br = Data.CWWW_CACHE[0] + Data.CWWW_CACHE[1]
                cold = int(all_ch_br * target_cold * 0.001)
                warm = int(all_ch_br * hue_precent * 0.001)
                #print("C: {}   W: {}".format(cold, warm))
                if Data.CWWW_CACHE[2] == 1 or wake:
                    # Write periphery
                    cw_obj.duty(cold)
                    ww_obj.duty(warm)
                Data.CWWW_CACHE[0] = cold if cold > 5 else 5
                Data.CWWW_CACHE[1] = warm if warm > 5 else 5
                my_task.out = f"HUE {int(hue_precent*0.1)}%w - CW:{cold} WW:{warm}"
                # Feed async loop
                await asyncio.sleep_ms(ms_period)
            __state_machine(cold, warm)
            my_task.out = f"HUE DONE {int(hue_precent*0.001)}%w - CW:{cold} WW:{warm}"

    if 0 <= percent <= 100:
        Data.TASK_STATE = True      # Save transition task is stared (kill param to overwrite task with user input)
        # Calculate actual brightness
        hue_ch = __cwww_init()[1].duty()
        hue_curr_percent = int((hue_ch / Data.CH_MAX) * 1000)
        # Create transition generator and calculate step_ms --- warm channel based dimming in time - aka automatic hue
        #print("Actual percent: {}, target percent: {}".format(actual_percent, warm_percent))
        hue_gen, step_ms = transition_gen(hue_curr_percent, percent*10, interval_sec=sec)
        # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
        state = micro_task(tag=Data.HUE_TASK_TAG, task=_task(ms_period=step_ms, iterable=hue_gen))
        return "Starting transition" if state else "Transition already running"
    else:
        return "Invalid range, percent=<0-100>"


def random(smooth=True, max_val=1000):
    """
    Demo function: implements random hue change
    :param smooth bool: enable smooth color transition: True(default)/False
    :param max_val: set channel maximum generated value: 0-1000
    :return dict: cct status - states: CW, WW, S
    """
    cold = randint(0, max_val)
    warm = randint(0, max_val)
    return white(cw=cold, ww=warm, smooth=smooth)


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
    :return dict: CW, WW, S
    """
    # Cold White / Warm White dedicated widget input - [OK]
    data = Data.CWWW_CACHE
    return {'CW': data[0], 'WW': data[1], 'S': data[2]}


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_dump(['cwhite', 'wwhite'])


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'white cw=<0-1000> ww=<0-1000> smooth=True force=True', \
           'toggle state=None smooth=True', 'load_n_init', \
           'brightness percent=<0-100> smooth=True wake=True', \
           'transition cw=None ww=None sec=1.0 wake=False',\
           'hue_transition percent=<0-100> sec=1.0 wake=False',\
           'random smooth=True max_val=1000', 'status', 'subscribe_presence', 'pinmap'
