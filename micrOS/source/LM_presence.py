from microIO import bind_pin, pinmap_search
from Common import SmartADC, micro_task, notify, syslog
from utime import ticks_ms
try:
    import LM_intercon as InterCon
except:
    InterCon = None

class Data:
    TASK_TAG = 'presence._capture'

    MIC_TYPES = {'NONE':0, 'ADC':1, 'I2S':2}
    MIC_TYPE = MIC_TYPES['NONE']      # Enable/Disable MIC periphery ('ADC', 'I2S', None)
    RAW_DATA = []               # format [[<time>, <amplitude>, <trigger>],...]
    MIC_ADC = None              # Initialized by micro task if sampled by ADC

    TIMER_VALUE = 120           # OFF action timer in sec
    OFF_EV_TIMER = 0            # Presence StateMachine
    TRIG_THRESHOLD = 3          # Presence StateMachine

    ON_CALLBACKS = set()        # Presence StateMachine - ON FUNCTION CALLBACK LIST
    OFF_CALLBACKS = set()       # Presence StateMachine - OFF FUNCTION CALLBACK LIST

    ON_INTERCON_CLBK = None     # Intercon ON callback
    OFF_INTERCON_CLBK = None    # Intercon OFF callback

    I2S_MIC = None              # Optional LM_i2s_mic import

    ENABLE_NOTIFY = False


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
            syslog(f"presence->__exec_local_callbacks: {e}")


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
            syslog(f"__run_intercon error: {e}")
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
            syslog(f"__run_intercon error: {e}")


####################################
# micrOS async task implementation #
####################################

async def __task(ms_period, buff_size):
    if Data.ENABLE_NOTIFY and not notify("Motion detected"):
        syslog("Motion detect. notify, error...")

    if Data.MIC_TYPE == Data.MIC_TYPES['ADC']:
        # Create ADC object
        Data.MIC_ADC = SmartADC.get_instance(bind_pin('mic'))
    elif Data.MIC_TYPE == Data.MIC_TYPES['I2S']:
        if Data.I2S_MIC is None:
            import LM_i2s_mic
            Data.I2S_MIC = LM_i2s_mic
        Data.I2S_MIC.load(sampling_rate=2000) # High frequencies can result in slow performance
        Data.I2S_MIC.background_capture()

    # ASYNC TASK ADAPTER [*2] with automatic state management
    #   [micro_task->Task] TaskManager access to task internals (out, done attributes)
    with micro_task(tag=Data.TASK_TAG) as my_task:
        while int(Data.OFF_EV_TIMER) > 0:
            if Data.MIC_TYPE:
                __mic_sample(buff_size, my_task)
            else:
                my_task.out = f"{int(Data.OFF_EV_TIMER)-1} sec until off event"
            Data.OFF_EV_TIMER -= round(ms_period / 1000, 3)
            # Async sleep - feed event loop
            await my_task.feed(sleep_ms=ms_period)

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


def __mic_sample(buff_size, mytask):
    """
    Async task to measure mic data
    - update OFF_EV_TIMER
        - threshold reached -> reset OFF_EV_TIMER to TIMER_VALUE
        - threshold not reached -> decrease OFF_EV_TIMER with deltaT
    - when OFF_EV_TIMER == 0 -> OFF event (+ exit task)
    """
    # [1] Measure mic signal + get time stump (tick_ms)
    timestamp = ticks_ms()

    if Data.MIC_TYPE == Data.MIC_TYPES['I2S']:
        samples = Data.I2S_MIC.get_from_buffer(Data.I2S_MIC.bytes_per_second(0.25))
        decoded_samples = Data.I2S_MIC.decode(samples)
        amplitude = 0 # 0-100 scale
        for s in decoded_samples:
            sample_normalized = 100 * abs(s)
            amplitude += sample_normalized / len(decoded_samples)
        data_triplet = [timestamp, amplitude, 0]

    elif Data.MIC_TYPE == Data.MIC_TYPES['ADC']:
        # Create average measurement sampling
        data_sum = 0
        # Internal sampling for average value calculation
        for _ in range(0, 15):
            data_sum += Data.MIC_ADC.get()['percent']  # raw, percent, volt
        data = data_sum / 15

        # Store data triplet
        data_triplet = [timestamp, data, 0]

    # Store data in task cache
    mytask.out = f"th: {Data.TRIG_THRESHOLD} last: {data_triplet} - timer: {int(Data.OFF_EV_TIMER)}"

    # Store data triplet (timestamp, mic_data)
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

def load(threshold=Data.TRIG_THRESHOLD, timer=Data.TIMER_VALUE, mic=Data.MIC_TYPE, enable_notify=False):
    """
    Initialize presence module
    :param threshold: trigger on relative noice change in percent
    :param timer: off timer in sec
    :param mic: enable / disable mic sampling (bool)
    :param enable_notify: enable (True) / disable (False) telegram notifications
    """
    threshold = threshold if threshold > 1 else 1
    Data.TRIG_THRESHOLD = threshold
    Data.TIMER_VALUE = timer
    Data.MIC_TYPE = mic
    Data.ENABLE_NOTIFY = enable_notify
    return f"Init presence module: th: {threshold} timer: {timer} mic: {mic} notify: {enable_notify}"


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
    return pinmap_search(['mic', 'irq1'])


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'load threshold=<percent> timer=<sec> mic=0 (0: None, 1: ADC, 2: I2S) enable_notify=False',\
           'motion_trig sample_ms=15 buff_size=10', 'get_samples',\
           'subscribe_intercon on="host cmd" off="host cmd"',\
           'pinmap'
