from sys import platform
from microIO import bind_pin, pinmap_search
from Common import transition_gen, micro_task
from utime import sleep_ms
from Types import resolve


#########################################
#     ANALOG DIMMER CONTROLLER PARAMS   #
#########################################
class Data:
    DIMMER_OBJ = None
    # DIMMER_CACHE: state:ON/OFF, value:0-1000
    DIMMER_CACHE = [0, 500]
    PERSISTENT_CACHE = False
    DIMM_TASK_TAG = "dimmer._tran"
    TASK_STATE = False


#########################################
#         ANALOG DIMMER WITH PWM        #
#########################################

def __dimmer_init():
    if Data.DIMMER_OBJ is None:
        from machine import Pin, PWM
        dimmer_pin = Pin(bind_pin('dim_1'))
        if platform == 'esp8266':
            Data.DIMMER_OBJ = PWM(dimmer_pin, freq=1024)
        else:
            Data.DIMMER_OBJ = PWM(dimmer_pin, freq=20480)
    return Data.DIMMER_OBJ


def __persistent_cache_manager(mode='r'):
    """
    pds - persistent data structure
    modes:
        r - recover, s - save
    """
    if not Data.PERSISTENT_CACHE:
        return
    if mode == 's':
        # SAVE CACHE
        with open('dimmer.pds', 'w') as f:
            f.write(','.join([str(k) for k in Data.DIMMER_CACHE]))
        return
    try:
        # RESTORE CACHE
        with open('dimmer.pds', 'r') as f:
            Data.DIMMER_CACHE = [int(data) for data in f.read().strip().split(',')]
    except:
        pass


def __state_machine(value):
    # State handling
    if value == 0:
        Data.DIMMER_CACHE[0] = 0                            # SAVE STATE TO CACHE
    else:
        Data.DIMMER_CACHE[1] = value if value > 5 else 5    # SAVE VALUE TO CACHE > 5 ! because toggle
        Data.DIMMER_CACHE[0] = 1                            # SAVE STATE TO CACHE
    __persistent_cache_manager('s')


#########################
# Application functions #
#########################

def load(cache=None):
    """
    Initialize dimmer module
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
    __persistent_cache_manager('r')
    if Data.PERSISTENT_CACHE and Data.DIMMER_CACHE[0] == 1:
        # Auto ON periphery if cache (loaded +) state ON
        set_value()
    else:
        # Auto OFF periphery
        set_value(0)
    return "CACHE: {}".format(Data.PERSISTENT_CACHE)


def set_value(value=None, smooth=True, force=True):
    """
    Set dimmer values with PWM signal
    :param value: (int) value 0-1000 default: None (set cached value)
    :param smooth: (bool) run channel change with smooth effect
    :param force: (bool) clean fade generators and set value
    :return dict: X, S
    """

    def __buttery(from_val, to_val):
        interval_sec = 0.2
        if Data.DIMMER_CACHE[0] == 0:
            # Turn from OFF to on (to whites)
            from_val = 0
            Data.DIMMER_CACHE[0] = 1
        # Create transition generator and calculate step_ms
        val_gen, step_ms = transition_gen(from_val, to_val, interval_sec=interval_sec)
        for _val in val_gen:
            __dimmer_init().duty(_val)
            sleep_ms(step_ms)

    if force:
        Data.TASK_STATE = False  # STOP TRANSITION TASK, SOFT KILL - USER INPUT PRIO

    # restore data from cache if it was not provided
    value = int(Data.DIMMER_CACHE[1] if value is None else value)
    if 0 <= value <= 1000:
        if smooth:
            # Set real-time smooth transition
            __buttery(Data.DIMMER_CACHE[1], value)
        else:
            # Set value immediately
            __dimmer_init().duty(value)
        __state_machine(value)
        return status()
    return "DIMMER ERROR, VALUE 0-1000 ONLY, GIVEN: {}".format(value)


def toggle(state=None, smooth=True):
    """
    Toggle dimmer state based on the stored state
    :param state bool: True(1)/False(0)/None(default - automatic toggle)
    :param smooth bool: run channel change with smooth effect
    :return dict: X, S
    """
    # Set state directly (inverse) + check change
    if state is not None:
        if bool(state) is bool(Data.DIMMER_CACHE[0]):
            return status()
        Data.DIMMER_CACHE[0] = 0 if state else 1

    if Data.DIMMER_CACHE[0] == 1:
        return set_value(0, smooth=smooth, force=False)         # Set value to 0 - OFF
    return set_value(smooth=smooth, force=False)                # Set value to the cached - ON


def transition(value, sec=1.0, wake=False):
    """
    [TASK] Set transition color change for long dimming periods < 30sec
    - creates the dimming generators
    :param value: value 0-1000
    :param sec: transition length in sec
    :param wake: bool, wake on setup (auto run on periphery)
    :return: info msg string
    """

    async def _task(ms_period, iterable):
        # [!] ASYNC TASK ADAPTER [*2] with automatic state management
        #   [micro_task->Task] TaskManager access to task internals (out, done attributes)
        with micro_task(tag=Data.DIMM_TASK_TAG) as my_task:
            for i in iterable:
                if not Data.TASK_STATE:                         # SOFT KILL TASK - USER INPUT PRIO
                    my_task.out = "Cancelled"
                    return
                if Data.DIMMER_CACHE[0] == 1 or wake:
                    # Write periphery
                    __dimmer_init().duty(i)
                # Update periphery cache (value check due to toggle ON value minimum)
                Data.DIMMER_CACHE[1] = i if i > 5 else 5   # SAVE VALUE TO CACHE > 5 ! because toggle
                my_task.out = f"Dimming: {i}"
                await my_task.feed(sleep_ms=ms_period)
            if Data.DIMMER_CACHE[0] == 1 or wake:
                __state_machine(i)
            my_task.out = f"Dimming DONE: {i}"

    Data.TASK_STATE = True      # Save transition task is stared (kill param to overwrite task with user input)
    if Data.DIMMER_CACHE[0] == 1:
        from_dim = __dimmer_init().duty()    # Get current value
    else:
        from_dim = Data.DIMMER_CACHE[1]
    # Create transition generator and calculate step_ms
    fade_gen, fade_step_ms = transition_gen(from_dim, value, interval_sec=sec)
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    state = micro_task(tag=Data.DIMM_TASK_TAG, task=_task(ms_period=fade_step_ms, iterable=fade_gen))
    return "Starting transition" if state else "Transition already running"


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
    :return dict: X, S
    """
    # Slider dedicated widget input - [OK]
    data = Data.DIMMER_CACHE
    return {'X': data[1], 'S': data[0]}


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_search('dim_1')


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('SLIDER set_value value=<0-1000> smooth=True force=True',
                             'BUTTON toggle state=<True,False> smooth=True',
                             'subscribe_presence',
                             'transition value=<0-1000> sec wake=False',
                             'status', 'load', 'pinmap'), widgets=widgets)
