OLED = None
DEBUG_CNT=0

def init():
    global OLED
    if OLED is None:
        import machine
        import ssd1306
        i2c = machine.I2C(-1, machine.Pin(5), machine.Pin(4))
        OLED = ssd1306.SSD1306_I2C(128, 64, i2c)

def text(intext="<text>", posx=0, posy=0, show=True):
    if OLED is None: init()
    OLED.text(intext, posx, posy)
    if show: OLED.show()
    return True

def invert(state=True):
    if OLED is None: init()
    OLED.invert(state)
    return True

def clean(state=0, show=True):
    if OLED is None: init()
    OLED.fill(state)
    if show: OLED.show()
    return True

def draw_line(sx, sy, ex, ey, state=1, show=True):
    if OLED is None: init()
    OLED.line(sx, sy, ex, ey, state)
    if show: OLED.show()
    return True

def draw_rect(sx, sy, ex, ey, state=1, show=True):
    if OLED is None: init()
    OLED.rect(sx, sy, ex, ey, state)
    if show: OLED.show()
    return True

def show_debug_page():
    global DEBUG_CNT
    try:
        from ConfigHandler import cfg
        from gc import mem_free
        clean()
        text("NW_MODE: {}".format(cfg.get("nwmd")), 0, 0, show=False)
        text("IP: {}".format(cfg.get("devip")), 0, 10, show=False)
        text("FreeMem: {}".format(mem_free()), 0, 20, show=False)
        text("PORT: {}".format(cfg.get("socport")), 0, 30, show=False)
        text("NAME: {}".format(cfg.get("devfid")), 0, 40, show=False)
        DEBUG_CNT+=1
        text("REFRESH: {}".format(DEBUG_CNT), 0, 50, show=True)
    except Exception as e:
        return str(e)

def wakeup_oled_debug_page_execute():
    from ConfigHandler import cfg
    if cfg.get("dbg"):
        show_debug_page()


