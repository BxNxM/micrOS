from LogicalPins import physical_pin, pinmap_dump
from Common import SmartADC, micro_task
import uasyncio as asyncio
from utime import ticks_ms
from Debug import errlog_add


class Data:
    TASK_TAG = 'mic_sample'
    RAW_DATA = []               # format [[<time>, <amplitude>, <trigger>],...]
    TIMER_VALUE = 50            # OFF action timer in sec
    OFF_EV_TIMER = 0            # Presence StateMachine
    OFF_CALLBACK = None         # Presence StateMachine
    ON_CALLBACK = None          # Presence StateMachine
    TRIG_THRESHOLD = 3          # Presence StateMachine


def threshold(th=Data.TRIG_THRESHOLD):
    """Set threshold value"""
    th = th if th > 1 else 1
    Data.TRIG_THRESHOLD = th
    return th


def subscribe(on, off, timer=50):
    """
    Load Module interface function to hook presence ON/OFF functions
    Set ON and OFF callbacks
        Hint: if callbacks have parameters wrap into lambda expression
    """
    Data.TIMER_VALUE = timer
    Data.ON_CALLBACK = on
    Data.OFF_CALLBACK = off


def motion_trig(sample_ms=30, buff_size=15):
    """
    Set motion trigger by IRQx - PIR sensor
    - Reset OFF_EV_TIMER to TIMER_VALUE
    - Start async mic sample task
    """
    # [1] RUN ON CALLBACK
    try:
        if Data.ON_CALLBACK is not None:
            Data.ON_CALLBACK()
    except Exception as e:
        errlog_add("[ON] presence->motion_trigger error: {}".format(e))

    # [2] (Re)Set timer counter value
    Data.OFF_EV_TIMER = Data.TIMER_VALUE

    # [3] Start mic sampling in async task
    create_task, _ = micro_task()
    state = create_task(callback=__mic_sample(sample_ms, buff_size), tag=Data.TASK_TAG)
    return "Starting" if state else "Already running"


def __eval_trigger():
    """
    Evaluate/Detect noise trigger
    """
    moving_avg = sum([k[1] for k in Data.RAW_DATA])/len(Data.RAW_DATA)
    if abs(moving_avg-Data.RAW_DATA[-1][1]) > Data.TRIG_THRESHOLD:
        return True


async def __mic_sample(sample_ms, buff_size):
    """
    Async task to measure mic data
    - update OFF_EV_TIMER
        - threshold reached -> reset OFF_EV_TIMER to TIMER_VALUE
        - threshold not reached -> decrease OFF_EV_TIMER with deltaT
    - when OFF_EV_TIMER == 0 -> OFF event (+ exit task)
    """
    _, tasks = micro_task()
    # Get my own task object to control output and state
    my_task = tasks.get(Data.TASK_TAG, None)

    # Create ADC object
    mic_adc = SmartADC.get_singleton(physical_pin('mic'))

    # Time window for mic sampling - reactivation
    while Data.OFF_EV_TIMER > 0:
        # [1] Measure mic signal + get time stump (tick_ms)
        time_stump = ticks_ms()

        # Create average measurement sampling
        data_sum = 0
        for _ in range(0, 50):
            data_sum += mic_adc.get()['percent']  # raw, percent, volt
        data = data_sum / 50
        
        # Store data triplet
        data_triplet = [time_stump, data, 0]

        # Store data in task cache
        if my_task is not None:
            my_task.out = "th: {} last data: {} - timer: {}".format(Data.TRIG_THRESHOLD, data_triplet, Data.OFF_EV_TIMER)

        # Store data triplet (time_stump, mic_data)
        Data.RAW_DATA.append(data_triplet)

        # Rotate results (based on buff size)
        if len(Data.RAW_DATA) > buff_size:
            Data.RAW_DATA = Data.RAW_DATA[-buff_size:]

        # [2] (Re)Set timer counter value
        if __eval_trigger():
            Data.OFF_EV_TIMER = Data.TIMER_VALUE
            data_triplet[2] = 1
        Data.OFF_EV_TIMER -= sample_ms/1000         # TODO

        # Async sleep - feed event loop
        await asyncio.sleep_ms(sample_ms)

    # [3]RUN OFF CALLBACK
    try:
        if Data.OFF_CALLBACK is not None:
            Data.OFF_CALLBACK()
    except Exception as e:
        errlog_add("[OFF] presence->__mic_sample error: {}".format(e))

    # Hack to detect task was stopped - SET Task obj done param to True
    my_task = tasks.get(Data.TASK_TAG, None)
    if my_task is not None:
        my_task.done = True


def get_samples():
    """
    [DEBUG] Return measured data set
    """
    return Data.RAW_DATA


#######################
# LM helper functions #
#######################

def pinmap():
    # Return module used PIN mapping
    return pinmap_dump(['mic', 'irq1'])


def help():
    return 'motion_trig sample_ms=30 buff_size=15', 'threshold th=3', 'get_samples', 'pinmap'
