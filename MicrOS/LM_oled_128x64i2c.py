__OLED = None

def __init():
    global __OLED
    from machine import Pin, I2C
    from ssd1306 import SSD1306_I2C
    from LogicalPins import getPlatformValByKey
    i2c = I2C(-1, Pin(getPlatformValByKey('i2c_scl')), Pin(getPlatformValByKey('i2c_sda')))
    __OLED = SSD1306_I2C(128, 64, i2c)
    return __OLED

def text(intext="<text>", posx=0, posy=0, show=True):
    if  __OLED is None: __init()
    __OLED.text(intext, posx, posy)
    if show: __OLED.show()
    return True

def invert(state=True):
    if  __OLED is None: __init()
    __OLED.invert(state)
    return True

def clean(state=0, show=True):
    if  __OLED is None: __init()
    __OLED.fill(state)
    if show: __OLED.show()
    return True

def draw_line(sx, sy, ex, ey, state=1, show=True):
    if  __OLED is None: __init()
    __OLED.line(sx, sy, ex, ey, state)
    if show: __OLED.show()
    return True

def draw_rect(sx, sy, ex, ey, state=1, show=True):
    if  __OLED is None: __init()
    __OLED.rect(sx, sy, ex, ey, state)
    if show: __OLED.show()
    return True

def show_debug_page():
    try:
        from ConfigHandler import cfgget
        from gc import mem_free
        from time import localtime
        clean()
        text("{}:{}:{}".format(localtime()[-5], localtime()[-4], localtime()[-3]), 30, 0, show=False)
        text("NW_MODE: {}".format(cfgget("nwmd")), 0, 10, show=False)
        text("IP: {}".format(cfgget("devip")), 0, 20, show=False)
        text("FreeMem: {}".format(mem_free()), 0, 30, show=False)
        text("PORT: {}".format(cfgget("socport")), 0, 40, show=False)
        text("NAME: {}".format(cfgget("devfid")), 0, 50, show=True)
    except Exception as e:
        return str(e)

def wakeup_oled_debug_page_execute():
    from ConfigHandler import cfgget
    if cfgget("dbg"):
        show_debug_page()

def poweron():
    if  __OLED is None: __init()
    __OLED.poweron()

def poweroff():
    if  __OLED is None: __init()
    clean()
    __OLED.poweroff()
