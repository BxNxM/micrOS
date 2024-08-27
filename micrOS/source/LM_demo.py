from random import randint
from Time import uptime
from Types import resolve
from microIO import detect_platform
from Common import console

CNT = 0


def _debug(func):
    """
    Debug wrapper
    - console logging
    - handled cmd counter (exec_info to get the value)
    """
    def __wrapper(*args, **kwargs):
        global CNT
        CNT += 1
        console("debug module cmd executed")     # + Progress LED
        return func(*args, **kwargs)
    return __wrapper


def load():
    """
    Initialize demo module
    """
    return "demo module - loaded"


@_debug
def hello(name="MrNobody"):
    return f"Hello {name}! This is a micrOS smart endpoint ☁️, running on {detect_platform()}.\
    \nFor more info call `demo links` function :D"


@_debug
def calculator(a, b, op="+"):
    if op.strip() == "+":
        return f"{a} + {b} = {a + b}"
    if op.strip() == "-":
        return f"{a} - {b} = {a - b}"
    if op.strip() == "/":
        return f"{a} / {b} = {round(a / b, 3)}"
    if op.strip() == "*":
        return f"{a} * {b} = {a * b}"


@_debug
def dice_cube():
    value = randint(1, 6)
    return f"🎲 {value}"


@_debug
def yes_no():
    val = randint(0, 1)
    return 'NO👎' if val == 0 else 'YES👍'


@_debug
def links():
    descript = f"Platform: {detect_platform()}\nGITHUB: https://github.com/BxNxM/micrOS\nYOUTUBE: https://www.youtube.com/@micrOSframework\nINSTAGRAM: https://instagram.com/micros_framework"
    return descript


@_debug
def source():
    return 'https://github.com/BxNxM/micrOS/blob/master/micrOS/source/LM_demo.py'


@_debug
def exec_info():
    global CNT
    return f"Under {uptime()}: {CNT} cmd served."


@_debug
def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('hello name="MrNobody"',
           'calculator a b op="+"',
           '\t=>op: + - / *',
           'BUTTON dice_cube',
           'dice_cube - show number, roll a dice',
           'BUTTON yes_no',
           'yes_no    - show random yes/no',
           'links     - show micrOS links',
           'source    - show demo module source code',
           'TEXTBOX exec_info',
           'exec_info - Execution info, demo module usage',
           'load'), widgets=widgets)
