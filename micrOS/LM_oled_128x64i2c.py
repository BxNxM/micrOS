from time import localtime, sleep

__OLED = None
__INVERT = False

def __init():
    global __OLED
    if __OLED is None:
        from machine import Pin, I2C
        from ssd1306 import SSD1306_I2C
        from LogicalPins import get_pin_on_platform_by_key
        i2c = I2C(-1, Pin(get_pin_on_platform_by_key('i2c_scl')), Pin(get_pin_on_platform_by_key('i2c_sda')))
        __OLED = SSD1306_I2C(128, 64, i2c)
    return __OLED


def text(intext="<text>", posx=0, posy=0, show=True):
    __init().text(intext, posx, posy)
    if show: __OLED.show()
    return True


def invert(state=None):
    global __INVERT
    __init()
    if state is not None:
        __OLED.invert(state)
    else:
        __INVERT = not __INVERT
        __OLED.invert(__INVERT)
    return True


def clean(state=0, show=True):
    __init().fill(state)
    if show: __OLED.show()
    return True


def draw_line(sx, sy, ex, ey, state=1, show=True):
    __init().line(sx, sy, ex, ey, state)
    if show: __OLED.show()
    return True


def draw_rect(sx, sy, ex, ey, state=1, show=True):
    __init().rect(sx, sy, ex, ey, state)
    if show: __OLED.show()
    return True


def poweron():
    __init().poweron()
    return True


def poweroff():
    __init().poweroff()
    return True


def help():
    return 'text', 'invert', 'clean', 'draw_line', 'draw_rect', 'poweron', 'poweroff'
