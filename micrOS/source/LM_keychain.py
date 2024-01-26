import LM_oled as oled
from LM_ds18 import measure
from LM_neopixel import color, brightness, toggle

INITED = False

def load_n_init():
    global INITED
    oled.load_n_init(64, 32)
    INITED = True


def display():
    # STA    H:M:S  W
    #    IP:    1.92
    #    Temp:  40C
    if not INITED:
        load_n_init()

    oled.text('STA 12:0:0', x=1, y=1)
    oled.text('IP: 1.92', x=4, y=10)
    oled.text(f"T[C]: {measure()}", x=4, y=20)
    oled.show()


def temperature():
    return measure()


def neopixel(r=None, g=None, b=None, br=None, onoff=None, smooth=True):
    if r is not None or g is not None or b is not None:
        return color(r, g, b, smooth=smooth)
    if br is not None:
        brightness(br, smooth=smooth)
    if onoff is not None:
        if onoff == 'toggle':
            return toggle(smooth=smooth)
        state = True if onoff == 'on' else False
        return toggle(state, smooth=smooth)


def lmdep():
    return 'oled', 'ds18', 'neopixel'


def help():
    return 'load_n_init', 'temperature', 'display', 'display &&1000'\
           'neopixel r=<0-255> g=<0-255> b=<0-255> br=<0-100> onoff=<toggle/on/off> smooth=<True/False>',\
           'lmdep'
