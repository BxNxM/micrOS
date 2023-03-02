"""
Module is responsible for collect the additional
feature definition dedicated to micrOS framework towards LoadModules

socket_stream decorator
- adds an extra msgobj to the wrapped function arg list
- msgobj provides socket msg interface for the open connection

Designed by Marcell Ban aka BxNxM
"""

from SocketServer import SocketServer
from machine import Pin, ADC
from sys import platform
from LogicalPins import physical_pin
from Debug import logger, log_get
try:
    from TaskManager import Task, Manager
except Exception as e:
    print("Import ERROR, TaskManager: {}".format(e))
    Task, Manager = None, None
try:
    from Notify import Telegram
except Exception as e:
    print("Import ERROR, Notify.Telegram: {}".format(e))
    Telegram = None


def socket_stream(func):
    """
    Provide socket message object as [msgobj]
    (SocketServer singleton class)
    """
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs, msgobj=SocketServer().reply_message)
    return wrapper


def transition(from_val, to_val, step_ms, interval_sec):
    """
    transition v1 (core)
    Generator for color transitions:
    :param from_val: from value - start from
    :param to_val: to value - target value
    :param step_ms: step to reach to_val - timirq_seq
    :param interval_sec: full intervals
    """
    if interval_sec > 0:
        step_cnt = round((interval_sec*1000)/step_ms)
        delta = abs((from_val-to_val)/step_cnt)
        direc = -1 if from_val > to_val else 1
        for cnt in range(0, step_cnt+1):
            yield round(from_val + (cnt * delta) * direc)
    else:
        yield round(to_val)


def transition_gen(*args, interval_sec=1.0):
    """
    transition v2
    Create multiple transition generators
    - calculate minimum step count -> step_ms
    - autofill and use use transition(from_val, to_val, step_ms, interval_sec)
    :param args: ch1_from, ch1_to, ch2_from, ch2_to, etc...
    :param interval_sec: interval in sec to calculate optimal fade/transition effect
    return: gen, step_ms OR gen list, step_ms
    """
    step_ms_min = 5            # min calculated step is 5 ms - good enough
    delta = max([abs(args[ch_from_i] - args[ch_from_i+1]) for ch_from_i in range(0, len(args)-1, 2)])
    step_ms = 0 if delta == 0 else int(interval_sec*1000 / delta)
    step_ms = step_ms_min if step_ms < step_ms_min else step_ms
    transitions = list([transition(args[ch_from_i], args[ch_from_i+1], step_ms, interval_sec) for ch_from_i in range(0, len(args)-1, 2)])
    if len(transitions) == 1:
        return transitions[0], step_ms
    return list(transitions), step_ms


class SmartADC:
    """
    ADC.ATTN_0DB: 0dB attenuation, gives a maximum input voltage of 1.00v - this is the default configuration
    ADC.ATTN_2_5DB: 2.5dB attenuation, gives a maximum input voltage of approximately 1.34v
    ADC.ATTN_6DB: 6dB attenuation, gives a maximum input voltage of approximately 2.00v
    ADC.ATTN_11DB: 11dB attenuation, gives a maximum input voltage of approximately 3.6v
    """
    OBJS = {}

    def __init__(self, pin):
        self.adc = None
        self.adp_prop = ()
        if not isinstance(pin, int):
            pin = physical_pin(pin)
        if 'esp8266' in platform:
            self.adc = ADC(pin)  # 1V measure range
            self.adp_prop = (1023, 1.0)
        else:
            self.adc = ADC(Pin(pin))
            self.adc.atten(ADC.ATTN_11DB)  # 3.3V measure range
            self.adp_prop = (4095, 3.6)

    def get(self):
        raw = self.adc.read()
        percent = raw / self.adp_prop[0]
        volt = round(percent * self.adp_prop[1], 1)
        return {'raw': raw, 'percent': round(percent*100, 1), 'volt': volt}

    @staticmethod
    def get_singleton(pin):
        if pin in SmartADC.OBJS.keys():
            return SmartADC.OBJS[pin]
        SmartADC.OBJS[pin] = SmartADC(pin)
        return SmartADC.OBJS[pin]


def micro_task(tag, task=None):
    """
    Async task creation from Load Modules
    - Indirect interface
    tag:
        [1] tag=None: return task generator object
        [2] tag=taskID: return existing task object by tag
    task: coroutine to execute (built in overload protection and lcm)
    """
    # [0] Check dependencies
    if Task is None or Manager is None:
        # RETURN: None - cannot utilize async task functionality
        return None
    if task is None:
        # [1] Task is None -> Get task mode by tag
        # RETURN task obj (access obj.out + obj.done (automatic - with keyword arg))
        async_task = Task.TASKS.get(tag, None)
        return async_task
    elif Task.task_is_busy(tag):
        # [2] Shortcut: Check task state by tag
        # RETURN: None - if task is already running
        return None
    else:
        # [3] Create task (not running) + task coroutine was provided
        # RETURN task creation state - success (True) / fail (False)
        state = Manager().create_task(callback=task, tag=tag)
        return state


@socket_stream
def data_logger(f_name, data=None, limit=12, msgobj=None):
    """
    micrOS Common Data logger solution
    - if data None => read mode
    - if data value => write mode
    :param f_name: log name (without extension, automatic: .dat)
    :param data: data to append
    :param limit: line limit (max.: 12 with short lines: limited disk speed!)
    :param msgobj: socket stream object (set automatically!)
    """
    # TODO: test!!!
    ext = '.dat'
    f_name = f_name if f_name.endswith(ext) else '{}{}'.format(f_name, ext)
    # GET LOGGED DATA
    if data is None:
        # return log as msg stream
        log_get(f_name, msgobj=msgobj)
        return True
    # ADD DATA TO LOG
    return logger(data, f_name, limit)


def notify(text):
    """
    micrOS common notification handler (Telegram)
    :param text: notification text
    return: verdict: True/False
    """
    if Telegram is None:
        return False
    try:
        out = Telegram().send_msg(text)
    except Exception as e:
        print("Notify ERROR: {}".format(e))
        out = str(e)
    if out is not None and out == 'Sent':
        return True
    return False
