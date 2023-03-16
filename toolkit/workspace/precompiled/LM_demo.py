from random import randint
from LogicalPins import detect_platform


def hello(name="MrNobody"):
    return f"Hello {name}! This is a micrOS smart endpoint ☁️, running on {detect_platform()}.\
    \nFor more info call `demo links` function :D"


def calculator(a, b, op="+"):
    if op.strip() == "+":
        return f"{a} + {b} = {a + b}"
    if op.strip() == "-":
        return f"{a} - {b} = {a - b}"
    if op.strip() == "/":
        return f"{a} / {b} = {round(a / b, 3)}"
    if op.strip() == "*":
        return f"{a} * {b} = {a * b}"


def dice_cube():
    value = randint(1, 6)
    return f"🎲 {value}"


def yes_no():
    val = randint(0, 1)
    return 'NO👎' if val == 0 else 'YES👍'


def links():
    descript = f"Platform: {detect_platform()}\nGITHUB: https://github.com/BxNxM/micrOS\nYOUTUBE: https://www.youtube.com/@micrOSframework\nINSTAGRAM: https://instagram.com/micros_framework"
    return descript


def source():
    return 'https://github.com/BxNxM/micrOS/blob/master/micrOS/source/LM_demo.py'


def help():
    return 'hello name="MrNobody"',\
           'calculator a b op="+"',\
           '\t=>op: + - / *',\
           'dice_cube - show number, roll a dice',\
           'yes_no    - show random yes/no',\
           'links     - show micrOS links',\
           'source    - show demo module source code'
