from LogicalPins import physical_pin, pinmap_dump
from Common import SmartADC, micro_task, notify
import uasyncio as asyncio
from utime import ticks_ms
from Debug import errlog_add
try:
    import LM_intercon as InterCon
except:
    InterCon = None


class Data:
    TASK_TAG = 'presence._mic'

    ENABLE_MIC = True           # Enable/Disable MIC periphery
    RAW_DATA = []               # format [[<time>, <amplitude>, <trigger>],...]

    TIMER_VALUE = 120           # OFF action timer in sec
    OFF_EV_TIMER = 0            # Presence StateMachine
    TRIG_THRESHOLD = 3          # Presence StateMachine

    ON_CALLBACKS = set()        # Presence StateMachine - ON FUNCTION CALLBACK LIST
    OFF_CALLBACKS = set()       # Presence StateMachine - OFF FUNCTION CALLBACK LIST

    ON_INTERCON_CLBK = None     # Intercon ON callback
    OFF_INTERCON_CLBK = None    # Intercon OFF callback

    NOTIFY = False


#######################################
#  Local and Remote callback handlers #
#######################################

def _subscribe(on, off):
    """
    [!!!!]
    Load Module interface function to hook presence ON/OFF functions
    Set ON and OFF callbacks
        Hint: if callbacks have parameters wrap into lambda expression
    """
    Data.ON_CALLBACKS.add(on)
    Data.OFF_CALLBACKS.add(off)


def __exec_local_callbacks(callback_list):
    """
    Run local callbacks - support multiple load module ON/OFF callback actions
    - callback_list: list of functions (without params) / lambda expression
    """
    # [1] RUN LOCAL CALLBACKS
    for clbk in callback_list:
        try:
            clbk()
        except Exception as e:
            errlog_add("presence->__exec_local_callbacks: {}".format(e))


def __run_intercon(state):
    """
    Run stored intercon ON/OFF commands
    state: on/off
    """
    if state.lower() == "on":
        if Data.ON_INTERCON_CLBK is None:
            return
        try:
            cmd = Data.ON_INTERCON_CLBK.split()
            host = cmd[0]
            cmd = ' '.join(cmd[1:])
            # Send CMD to other device & show result
            InterCon.send_cmd(host, cmd)
        except Exception as e:
            errlog_add("__run_intercon error: {}".format(e))
    if state.lower() == "off":
        if Data.OFF_INTERCON_CLBK is None:
            return
        try:
            cmd = Data.OFF_INTERCON_CLBK.split()
            host = cmd[0]
            cmd = ' '.join(cmd[1:])
            # Send CMD to other device & show result
            InterCon.send_cmd(host, cmd)
        except Exception as e:
            errlog_add("__run_intercon error: {}".format(e))


####################################
# micrOS async task implementation #
####################################

async def __task(ms_period, buff_size):
    if Data.NOTIFY:
        if not notify("Motion detected"):
            errlog_add("Motion detect. notify, error...")

    if Data.ENABLE_MIC:
        # Create ADC object
        mic_adc = SmartADC.get_singleton(physical_pin('mic'))

    # ASYNC TASK ADAPTER [*2] with automatic state management
    #   [micro_task->Task] TaskManager access to task internals (out, done attributes)
    with micro_task(tag=Data.TASK_TAG) as my_task:
        while int(Data.OFF_EV_TIMER) > 0:
            if Data.ENABLE_MIC:
                __mic_sample(buff_size=buff_size, mic_adc=mic_adc, mytask=my_task)
            else:
                my_task.out = "{} sec until off event".format(int(Data.OFF_EV_TIMER)-1)
            Data.OFF_EV_TIMER -= round(ms_period / 1000, 3)
            # Async sleep - feed event loop
            await asyncio.sleep_ms(ms_period)

        # RUN OFF CALLBACK (local + remote)
        __exec_local_callbacks(Data.OFF_CALLBACKS)
        __run_intercon('off')


#########################
#      MIC HANDLING     #
#########################

def __eval_trigger():
    """
    Evaluate/Detect noise trigger
    """
    moving_avg = round(sum([k[1] for k in Data.RAW_DATA])/len(Data.RAW_DATA), 4)
    if abs(moving_avg-Data.RAW_DATA[-1][1]) > Data.TRIG_THRESHOLD:
        return True


def __mic_sample(buff_size, mic_adc, mytask):
    """
    Async task to measure mic data
    - update OFF_EV_TIMER
        - threshold reached -> reset OFF_EV_TIMER to TIMER_VALUE
        - threshold not reached -> decrease OFF_EV_TIMER with deltaT
    - when OFF_EV_TIMER == 0 -> OFF event (+ exit task)
    """

    # [1] Measure mic signal + get time stump (tick_ms)
    time_stump = ticks_ms()

    # Create average measurement sampling
    data_sum = 0
    # Internal sampling for average value calculation
    for _ in range(0, 15):
        data_sum += mic_adc.get()['percent']  # raw, percent, volt
    data = data_sum / 15
        
    # Store data triplet
    data_triplet = [time_stump, data, 0]

    # Store data in task cache
    mytask.out = "th: {} last: {} - timer: {}".format(Data.TRIG_THRESHOLD, data_triplet, int(Data.OFF_EV_TIMER))

    # Store data triplet (time_stump, mic_data)
    Data.RAW_DATA.append(data_triplet)

    # Rotate results (based on buff size)
    if len(Data.RAW_DATA) > buff_size:
        Data.RAW_DATA = Data.RAW_DATA[-buff_size:]

    # [2] (Re)Set timer counter value
    if __eval_trigger():
        Data.OFF_EV_TIMER = Data.TIMER_VALUE
        data_triplet[2] = 1


##############################
#  PRESENCE PUBLIC FUNCTIONS #
##############################

def load_n_init(threshold=Data.TRIG_THRESHOLD, timer=Data.TIMER_VALUE, mic=Data.ENABLE_MIC):
    """
    Initialize presence module
    :param threshold: trigger on relative noice change in percent
    :param timer: off timer in sec
    :param mic: enable / disable mic sampling (bool)
    """
    threshold = threshold if threshold > 1 else 1
    Data.TRIG_THRESHOLD = threshold
    Data.TIMER_VALUE = timer
    Data.ENABLE_MIC = mic
    return "Init presence module: th: {} timer: {} mic: {}".format(threshold, timer, mic)


def motion_trig(sample_ms=15, buff_size=10):
    """
    Set motion trigger by IRQx - PIR sensor
    - Reset OFF_EV_TIMER to TIMER_VALUE
    - Start async mic sample task
    """
    # [1] RUN ON CALLBACK
    __exec_local_callbacks(Data.ON_CALLBACKS)
    __run_intercon('on')

    # [2] (Re)Set timer counter value
    Data.OFF_EV_TIMER = Data.TIMER_VALUE

    # [3] Start mic sampling in async task
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    state = micro_task(tag=Data.TASK_TAG, task=__task(ms_period=sample_ms, buff_size=buff_size))
    return "Starting" if state else "Already running"


def subscribe_intercon(on, off):
    """
    Subscribe function for remote function execution
    - intercon ON/OFF string callbacks
        ON: host cmd
        OFF: host cmd
    """
    Data.ON_INTERCON_CLBK = on
    Data.OFF_INTERCON_CLBK = off
    return {'on': Data.ON_INTERCON_CLBK, 'off': Data.OFF_INTERCON_CLBK}


def notification(state=None):
    """Enable/Disable motion detection notifications"""
    if state is None:
        return "Notifications: {}".format("enabled" if Data.NOTIFY else "disabled")
    Data.NOTIFY = True if state else False
    return "Set notifications: {}".format("ON" if Data.NOTIFY else "OFF")


def get_samples():
    """
    [DEBUG] Return measured data set
    """
    return Data.RAW_DATA


#######################
# LM helper functions #
#######################

def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_dump(['mic', 'irq1'])


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'load_n_init threshold=<percent> timer=<sec> mic=True',\
           'motion_trig sample_ms=15 buff_size=10', 'get_samples',\
           'subscribe_intercon on="host cmd" off="host cmd"',\
           'notification state=None/True/False',\
           'pinmap'
