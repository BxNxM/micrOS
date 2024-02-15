from utime import localtime
from Network import ifconfig
from LM_oled import text, show, rect, clean, load_n_init as oled_lni
from LM_ds18 import measure
from LM_neopixel import color, brightness, toggle, load_n_init as neopixel_lni

INITED = False


def load_n_init():
    """
    Init OLED display 64x32
    """
    global INITED
    neopixel_lni(ledcnt=1)
    try:
        oled_lni(128, 64)
        INITED = True
        return "OLED INIT OK"
    except Exception as e:
        INITED = False
        return f"OLED INIT NOK: {e}"


def display():
    """
    Run display content refresh
        STA    H:M:S  W
          IP:   1.92
          T[C]: 40C
    """

    if not INITED:
        _v = load_n_init()
        if not INITED:
            return _v

    # Clean display and draw rect...
    clean()
    rect(0, 0, 66, 34)
    ltime = localtime()
    h = "0{}".format(ltime[-5]) if len(str(ltime[-5])) < 2 else ltime[-5]
    m = "0{}".format(ltime[-4]) if len(str(ltime[-4])) < 2 else ltime[-4]
    s = "0{}".format(ltime[-3]) if len(str(ltime[-3])) < 2 else ltime[-3]
    nwmd, nwif = ifconfig()
    nwmd, devip = nwmd[0] if len(nwmd) > 0 else "0", ".".join(nwif[0].split(".")[-2:])

    # Draw data to display
    text(f"{h}:{m}:{s}", x=0, y=1)
    text(f"{nwmd}: {devip}", x=4, y=10)
    text(f"{round(tuple(measure().values())[0], 1)} C", x=4, y=20)
    show()
    return "Display show"


def temperature():
    """
    Measure ds18B20 temperature sensor
    """
    return measure()


def neopixel(r=None, g=None, b=None, br=None, onoff=None, smooth=True):
    """
    Set neopixel LED colors
    """
    if r is not None or g is not None or b is not None:
        return color(r, g, b, smooth=smooth)
    if br is not None:
        brightness(br, smooth=smooth)
    if onoff is not None:
        if onoff == "toggle":
            return toggle(smooth=smooth)
        state = True if onoff == 'on' else False
        return toggle(state, smooth=smooth)
    return 'No action: r g b br onoff smooth'


def lmdep():
    """
    Load Module dependencies
    """
    return 'oled', 'ds18', 'neopixel'


def pinmap():
    """
    PIN MAP dump
    """
    from LM_oled import pinmap as o_pmp
    from LM_ds18 import pinmap as t_pmp
    from LM_neopixel import pinmap as n_pmp
    pmp = o_pmp()
    pmp.update(t_pmp())
    pmp.update(n_pmp())
    return pmp


def help():
    return 'load_n_init', 'temperature', 'display', 'display &&1000',\
           'neopixel r=<0-255> g=<0-255> b=<0-255> br=<0-100> onoff=<toggle/on/off> smooth=<True/False>',\
           'pinmap', 'lmdep'
