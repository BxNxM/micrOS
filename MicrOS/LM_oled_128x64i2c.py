OLED = None

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
    try:
        from ConfigHandler import cfg
        from gc import mem_free
        text("NW_MODE: {}".format(cfg.get("nw_mode")), 0, 0)
        text("IP: {}".format(cfg.get("dev_ipaddr")), 0, 10)
        text("FreeMem: {}".format(mem_free()), 0, 20)
    except Exception as e:
        return str(e)


