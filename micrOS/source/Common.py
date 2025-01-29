"""
micrOS Load Module programming Official API-s
    Designed by Marcell Ban aka BxNxM
"""

from Server import Server, WebCli
from Debug import errlog_add, console_write
from Logger import logger, log_get
from microIO import resolve_pin
from Tasks import TaskBase, Manager, lm_exec
from machine import Pin, ADC
from Notify import Notify

################## Common LM features ##################

def transition(from_val, to_val, step_ms, interval_sec):
    """
    [LM] Single Generator for color/value transition:
    :param from_val: from value - start from
    :param to_val: to value - target value
    :param step_ms: step to reach to_val - timirq_seq
    :param interval_sec: time of full interval
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
    [LM] Multiple Generator for color/value transitions:
    - calculate minimum step count -> step_ms
    - autofill and use transition(from_val, to_val, step_ms, interval_sec)
    :param args: ch1_from, ch1_to, ch2_from, ch2_to, etc...
    :param interval_sec: interval in sec to calculate optimal fade/transition effect
    return: gen, step_ms OR gen list, step_ms
    """
    step_ms_min = 5            # min calculated step is 5 ms - good enough
    delta = max((abs(args[ch_from_i] - args[ch_from_i+1]) for ch_from_i in range(0, len(args)-1, 2)))
    step_ms = 0 if delta == 0 else int(interval_sec*1000 / delta)
    step_ms = step_ms_min if step_ms < step_ms_min else step_ms
    transitions = list((transition(args[ch_from_i], args[ch_from_i+1], step_ms, interval_sec) for ch_from_i in range(0, len(args)-1, 2)))
    if len(transitions) == 1:
        return transitions[0], step_ms
    return list(transitions), step_ms


class SmartADC:
    """
    [LM] General ADC implementation for auto scaled output: raw, percent, volt
    https://docs.micropython.org/en/latest/esp32/quickref.html#adc-analog-to-digital-conversion
        ADC.ATTN_0DB: 0 dB attenuation, resulting in a full-scale voltage range of 0-1.1V
        ADC.ATTN_2_5DB: 2.5 dB ... of 0-1.5V
        ADC.ATTN_6DB: 6 dB ... of 0-2.2V
        ADC.ATTN_11DB: 11 dB ... of 0-2450mV/
    Note that the absolute maximum voltage rating for input pins is 3.6V. Going near to this boundary risks damage to the IC!
    """
    OBJS = {}

    def __init__(self, pin):
        self.adp_prop = (65535, 2450)                               # raw value, 2450mV (so 2,45V)
        self.adc = None
        if not isinstance(pin, int):
            pin = resolve_pin(pin)
        self.adc = ADC(Pin(pin))
        self.adc.atten(ADC.ATTN_11DB)                               # 2450mV measure range

    def get(self):
        raw = int((self.adc.read_u16() + self.adc.read_u16())/2)    # 16-bit ADC value (0-65535)
        percent = raw / self.adp_prop[0]
        volt = round(percent * self.adp_prop[1] / 1000, 2)          # devide with 1000 to get V from mV
        return {'raw': raw, 'percent': round(percent*100, 1), 'volt': volt}

    @staticmethod
    def get_instance(pin):
        if pin in SmartADC.OBJS.keys():
            return SmartADC.OBJS[pin]
        SmartADC.OBJS[pin] = SmartADC(pin)
        return SmartADC.OBJS[pin]

################# micrOS feature interfaces #################

def micro_task(tag, task=None):
    """
    [LM] Async task creation
    :param tag:
        [1] tag=None: return task generator object
        [2] tag=taskID: return existing task object by tag
    :param task: coroutine to execute (with built-in overload protection and lcm)
    """
    if task is None:
        # [1] Task is None -> Get task mode by tag
        # RETURN task obj (access obj.out + obj.done (automatic - with keyword arg))
        async_task = TaskBase.TASKS.get(tag, None)
        return async_task
    if TaskBase.is_busy(tag):
        # [2] Shortcut: Check task state by tag
        # RETURN: None - if task is already running
        return None
    # [3] Create task (not running) + task coroutine was provided
    # RETURN task creation state - success (True) / fail (False)
    state = Manager().create_task(callback=task, tag=tag)
    return state


def manage_task(tag, operation):
    """
    [LM] Async task management
    :param tag: task tag
    :param operation: kill / show / isbusy
    """
    if Manager is None:
        # RETURN: None - cannot utilize async task functionality
        return None
    if operation == "show":
        return str(Manager().show(tag=tag))
    if operation == "kill":
        return Manager().kill(tag=tag)
    if operation == "isbusy":
        return TaskBase.is_busy(tag=tag)
    raise Exception(f"Invalid operation: {operation}")


def exec_cmd(cmd, skip_check=False):
    """
    [LM] Single (sync) LM execution
    :param cmd: command string list
    :param skip_check: skip cmd type check, micropython bug
    return state, output
    """
    # [BUG] Solution with isinstance/type is not reliable... micropython 1.22
    #          Invalid type, must be list: <class list>" ...
    if skip_check:
        return lm_exec(cmd)
    return lm_exec(cmd) if isinstance(cmd, list) else False, f"Invalid type, must be list: {type(cmd)}"


def notify(text=None) -> bool:
    """
    [LM] micrOS common notification handler (Telegram)
    :param text: notification text / None (return notification state)
    return: verdict: True/False
    """
    # (1) Return notification state
    if text is None:
        return Notify.GLOBAL_NOTIFY
    # (2) Send notification
    try:
        out = Notify.notify(text)
    except Exception as e:
        errlog_add(f"[ERR] Notify: {e}")
        out = str(e)
    if out is not None and (out.startswith('Sent') or out.endswith('disabled')):
        return True
    return False


def web_endpoint(endpoint, function) -> bool:
    """
    [LM] Add test endpoint <localhost.local>/endpoint from Load Modules
    :param endpoint: simple string, name of the endpoint
    :param function:
        [1] Normal function return tuple (html_type, data):
            image/jpeg | text/html | text/plain, <data>
                                                 <data>: binary | string
        [2] Stream function return tuple (multipart_type, data):
            multipart/x-mixed-replace | multipart/form-data, <data>
                <data>: {'callback':<func>, 'content-type': image/jpeg | audio/l16;*}
    """
    WebCli.register(endpoint=endpoint, callback=function)
    return True


def socket_stream(func):
    """
    [LM] Decorator for Socket message stream - adds msgobj to the decorated function arg list.
    Use msgobj as print function: msgobj("hello")
    (Server singleton class - reply all bug/feature)
    """
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs, msgobj=Server.reply_all)
    return wrapper


@socket_stream
def data_logger(f_name, data=None, limit=12, msgobj=None):
    """
    [LM] micrOS Common Data logger solution
    - if data None => read mode
    - if data value => write mode
    :param f_name: log name (without extension, automatic: .dat)
    :param data: data to append
    :param limit: line limit (max.: 12 with short lines: limited disk speed!)
    :param msgobj: socket stream object (set automatically!)
    """
    f_name = f_name if f_name.endswith('.dat') else f'{f_name}.dat'
    # GET LOGGED DATA
    if data is None:
        # return log as msg stream
        log_get(f_name, msgobj=msgobj)
        return True
    # ADD DATA TO LOG
    return logger(data, f_name, limit)


def syslog(msg):
    """ Wrapper of errlog_add """
    return errlog_add(f"{msg}")


def console(msg):
    """ Wrapper of console_write """
    return console_write(msg)
