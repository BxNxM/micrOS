__OLED = None

def __init():
    global __OLED
    if __OLED is None:
        import machine
        import ssd1306
        i2c = machine.I2C(-1, machine.Pin(5), machine.Pin(4))
        __OLED = ssd1306.SSD1306_I2C(128, 64, i2c)

def text(intext="<text>", posx=0, posy=0, show=True):
    if __OLED is None: __init()
    __OLED.text(intext, posx, posy)
    if show: __OLED.show()
    return True

def invert(state=True):
    if __OLED is None: __init()
    __OLED.invert(state)
    return True

def clean(state=0, show=True):
    if __OLED is None: __init()
    __OLED.fill(state)
    if show: __OLED.show()
    return True

def draw_line(sx, sy, ex, ey, state=1, show=True):
    if __OLED is None: __init()
    __OLED.line(sx, sy, ex, ey, state)
    if show: __OLED.show()
    return True

def draw_rect(sx, sy, ex, ey, state=1, show=True):
    if __OLED is None: __init()
    __OLED.rect(sx, sy, ex, ey, state)
    if show: __OLED.show()
    return True

def show_debug_page():
    try:
        from ConfigHandler import cfg
        from gc import mem_free
        from time import localtime
        clean()
        text("{}:{}:{}".format(localtime()[-5], localtime()[-4], localtime()[-3]), 30, 0, show=False)
        text("NW_MODE: {}".format(cfg.get("nwmd")), 0, 10, show=False)
        text("IP: {}".format(cfg.get("devip")), 0, 20, show=False)
        text("FreeMem: {}".format(mem_free()), 0, 30, show=False)
        text("PORT: {}".format(cfg.get("socport")), 0, 40, show=False)
        text("NAME: {}".format(cfg.get("devfid")), 0, 50, show=True)
    except Exception as e:
        return str(e)

def wakeup_oled_debug_page_execute():
    from ConfigHandler import cfg
    if cfg.get("dbg"):
        show_debug_page()

def poweron():
    if __OLED is None: __init()
    __OLED.poweron()

def poweroff():
    if __OLED is None: __init()
    __OLED.poweroff()

def __deinit():
    global __OLED
    if __OLED is not None:
        clean
        poweroff()
        __OLED = None
