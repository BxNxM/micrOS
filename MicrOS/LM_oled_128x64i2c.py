def __init():
    import machine
    import ssd1306
    from LogicalPins import getPlatformValByKey
    i2c = machine.I2C(-1, machine.Pin(getPlatformValByKey('i2c_scl')), machine.Pin(getPlatformValByKey('i2c_sda')))
    return ssd1306.SSD1306_I2C(128, 64, i2c)

def text(intext="<text>", posx=0, posy=0, show=True, oledObj=None):
    if oledObj is None:
        __OLED = __init()
    else:
        __OLED = oledObj
    __OLED.text(intext, posx, posy)
    if show: __OLED.show()
    return True

def invert(state=True, oledObj=None):
    if oledObj is None:
        __OLED = __init()
    else:
        __OLED = oledObj
    __OLED.invert(state)
    return True

def clean(state=0, show=True, oledObj=None):
    if oledObj is None:
        __OLED = __init()
    else:
        __OLED = oledObj
    __OLED.fill(state)
    if show: __OLED.show()
    return True

def draw_line(sx, sy, ex, ey, state=1, show=True, oledObj=None):
    if oledObj is None:
        __OLED = __init()
    else:
        __OLED = oledObj
    __OLED.line(sx, sy, ex, ey, state)
    if show: __OLED.show()
    return True

def draw_rect(sx, sy, ex, ey, state=1, show=True, oledObj=None):
    if oledObj is None:
        __OLED = __init()
    else:
        __OLED = oledObj
    __OLED.rect(sx, sy, ex, ey, state)
    if show: __OLED.show()
    return True

def show_debug_page():
    try:
        from ConfigHandler import cfgget
        from gc import mem_free
        from time import localtime
        oledObj = __init()
        clean(oledObj=oledObj)
        text("{}:{}:{}".format(localtime()[-5], localtime()[-4], localtime()[-3]), 30, 0, show=False, oledObj=oledObj)
        text("NW_MODE: {}".format(cfgget("nwmd")), 0, 10, show=False, oledObj=oledObj)
        text("IP: {}".format(cfgget("devip")), 0, 20, show=False, oledObj=oledObj)
        text("FreeMem: {}".format(mem_free()), 0, 30, show=False, oledObj=oledObj)
        text("PORT: {}".format(cfgget("socport")), 0, 40, show=False, oledObj=oledObj)
        text("NAME: {}".format(cfgget("devfid")), 0, 50, show=True, oledObj=oledObj)
    except Exception as e:
        return str(e)

def wakeup_oled_debug_page_execute():
    from ConfigHandler import cfgget
    if cfgget("dbg"):
        show_debug_page()

def poweron():
    __OLED = __init()
    __OLED.poweron()

def poweroff():
    __OLED = __init()
    clean(oledObj=__OLED)
    __OLED.poweroff()
