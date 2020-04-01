from ConfigHandler import cfgget
from gc import mem_free
from time import localtime, sleep

__OLED = None
__INVERT = False

def __init():
    global __OLED
    if __OLED is None:
        from machine import Pin, I2C
        from ssd1306 import SSD1306_I2C
        from LogicalPins import getPlatformValByKey
        i2c = I2C(-1, Pin(getPlatformValByKey('i2c_scl')), Pin(getPlatformValByKey('i2c_sda')))
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


def show_debug_page():
    try:
        clean(show=True)
        text("{}:{}:{}".format(localtime()[-5], localtime()[-4], localtime()[-3]), 30, 0, show=False)
        text("NW_MODE: {}".format(cfgget("nwmd")), 0, 10, show=False)
        text("IP: {}".format(cfgget("devip")), 0, 20, show=False)
        text("FreeMem: {}".format(mem_free()), 0, 30, show=False)
        text("PORT: {}".format(cfgget("socport")), 0, 40, show=False)
        text("NAME: {}".format(cfgget("devfid")), 0, 50, show=True)
    except Exception as e:
        return str(e)
    return True


def simple_page():

    try:
        clean()
        text("{}:{}:{}".format(localtime()[-5], localtime()[-4], localtime()[-3]), 30, 10, show=False)
        pixel_art()
    except Exception as e:
        return str(e)

    return True


def pixel_art():
    base_point = (55, 40)
    base_size = 15
    delta_size = 5

    # MAIN RECT
    draw_rect(base_point[0]-delta_size, base_point[1]-delta_size, base_size+delta_size, base_size+delta_size)
    sleep(0.15)

    # TOP-LEFT CORNER
    draw_rect(base_point[0]-delta_size, base_point[1]-delta_size, base_size, base_size)
    sleep(0.15)
    # BUTTON-RIGHT CORNER
    draw_rect(base_point[0], base_point[1], base_size, base_size)
    sleep(0.15)

    # TOP-LEFT CORNER2
    draw_rect(base_point[0]-delta_size, base_point[1]-delta_size, base_size-delta_size, base_size-delta_size)
    sleep(0.15)
    # BUTTON-RIGHT CORNER2
    draw_rect(base_point[0]+delta_size, base_point[1]+delta_size, base_size-delta_size, base_size-delta_size)
    sleep(0.15)

    # TOP-LEFT CORNER3
    draw_rect(base_point[0]-delta_size, base_point[1]-delta_size, base_size-delta_size*2, base_size-delta_size*2)
    sleep(0.15)
    # BUTTON-RIGHT CORNER3
    draw_rect(base_point[0]+delta_size*2, base_point[1]+delta_size*2, base_size-delta_size*2, base_size-delta_size*2)
    sleep(0.15)

    # Jumping cube - top-left - and back
    draw_rect(base_point[0]-delta_size*2, base_point[1]-delta_size*2, base_size-delta_size*2, base_size-delta_size*2)
    draw_rect(base_point[0]-delta_size, base_point[1]-delta_size, base_size-delta_size*2, base_size-delta_size*2, 0)      #
    sleep(0.1)
    draw_rect(base_point[0]-delta_size*3, base_point[1]-delta_size*3, base_size-delta_size*2, base_size-delta_size*2)
    draw_rect(base_point[0]-delta_size*2, base_point[1]-delta_size*2, base_size-delta_size*2, base_size-delta_size*2, 0)    #
    sleep(0.1)
    draw_rect(base_point[0]-delta_size*4, base_point[1]-delta_size*4, base_size-delta_size*2, base_size-delta_size*2)
    draw_rect(base_point[0]-delta_size*3, base_point[1]-delta_size*3, base_size-delta_size*2, base_size-delta_size*2, 0)    #
    sleep(0.1)
    draw_rect(base_point[0]-delta_size*4, base_point[1]-delta_size*4, base_size-delta_size*2, base_size-delta_size*2)
    draw_rect(base_point[0]-delta_size*4, base_point[1]-delta_size*4, base_size-delta_size*2, base_size-delta_size*2, 0)    #
    sleep(0.1)
    draw_rect(base_point[0]-delta_size*3, base_point[1]-delta_size*3, base_size-delta_size*2, base_size-delta_size*2)
    draw_rect(base_point[0]-delta_size*4, base_point[1]-delta_size*4, base_size-delta_size*2, base_size-delta_size*2, 0)
    sleep(0.1)
    draw_rect(base_point[0]-delta_size*2, base_point[1]-delta_size*2, base_size-delta_size*2, base_size-delta_size*2)
    draw_rect(base_point[0]-delta_size*3, base_point[1]-delta_size*3, base_size-delta_size*2, base_size-delta_size*2, 0)
    sleep(0.1)
    draw_rect(base_point[0]-delta_size, base_point[1]-delta_size, base_size-delta_size*2, base_size-delta_size*2)
    draw_rect(base_point[0]-delta_size*2, base_point[1]-delta_size*2, base_size-delta_size*2, base_size-delta_size*2, 0)
    invert()


def poweron():
    __init().poweron()
    return True


def poweroff():
    __init().poweroff()
    return True


def help():
    return ('text', 'invert', 'clean', 'draw_line', 'draw_rect', 'show_debug_page', 'simple_page', 'poweron', 'poweroff')
