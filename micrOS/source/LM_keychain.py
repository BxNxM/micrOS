import uasyncio as asyncio
from Common import micro_task
from utime import localtime
from Network import ifconfig
from LM_oled import text, show, rect, pixel, clean, load_n_init as oled_lni
from LM_ds18 import measure
from LM_neopixel import color, brightness, toggle, load_n_init as neopixel_lni
try:
    from LM_gameOfLife import next_gen as gol_nextgen, reset as gol_reset
except:
    gol_nextgen = None      # Optional function handling

class KC:
    INITED = False
    DP_main_page = True          # store display logical state: ON (main page) / OFF
    DP_cnt = 0              # display "count back", when 0 go to sleep -> OFF
    DP_cnt_default = None   # store calculated sequence to sleep 30sec/period_ms


def _screen_saver(scale=2):
    """
    Conway's game of life screen saver simulation
    :param scale: default (2) game of life matrix (16x32) upscale to real display size 32x64
    """
    # Default mode
    if gol_nextgen is None:
        return      # screen off - no screen saver...
    # Screen saver mode
    matrix = gol_nextgen(raw=True)
    if matrix is None:
        # Reset Game of life
        gol_reset()
    else:
        # Update display with Conway's Game of Life
        clean()
        for line_idx, line in enumerate(matrix):
            for x_idx, v in enumerate(line):
                if scale == 1:
                    pixel(x_idx, line_idx, color=v)
                else:
                    rect(x_idx*scale, line_idx*scale, w=scale, h=scale, state=v, fill=True)
        show()


async def _main_page(vd=False):
    """
    Run display content refresh
        H:M:S
         S/A: 1.92
         40.0 C
    """
    # Clean display and draw rect...
    clean()
    # Virtual display rectangle 64x32
    if vd:
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


async def __task(period_ms, vd=False):
    """
    Async display refresh task
    - main page    (main mode)  - auto sleep after 30 sec
    - screen saver (sleep mode)
    """
    # Auto init keychain module (if needed) - failsafe
    if not KC.INITED:
        _v = load_n_init()
        if not KC.INITED:
            return _v

    KC.DP_cnt_default = int(30_000 / period_ms)     # After 30 sec go to sleep mode
    KC.DP_cnt = KC.DP_cnt_default                   # Set sleep counter
    fast_period = int(period_ms/2)                  # Calculate faster refresh period

    # Run keychain main async loop, with update ID: kc._display
    with micro_task(tag="kc._display") as my_task:
        while True:
            if KC.DP_main_page:
                # [MAIN MODE] Execute main page
                await _main_page(vd=vd)                     #1 Run main page function
                my_task.out = f'main page: {KC.DP_cnt}'     #2 Update task data for (task show kc._display)
                KC.DP_cnt -= 1                              #3 Update sleep counter
                # Async sleep - feed event loop
                await asyncio.sleep_ms(period_ms)
            else:
                # [SLEEP MODE] Execute screen saver page
                _screen_saver()                             # Run sleep page function
                # Async sleep - feed event loop
                await asyncio.sleep_ms(fast_period)

            # Auto sleep event handler - off event - go to (sleep mode)
            if KC.DP_cnt <= 0:
                KC.DP_main_page = False         #1 disable main screen
                clean()                         #2 clean screen
                show()                          #3 show cleaned display
                KC.DP_cnt = KC.DP_cnt_default   #4 reset sleep counter to default
                my_task.out = 'sleep...'        


def _boot_page(msg):
    clean()
    msg_len = len(msg)*8                # message text length in pixels
    x_offset = int((64 - msg_len)/2)    # x (width) center-ing offset
    text(msg, x=x_offset, y=11)         # y(height):32 TODO: Auto positioning in y axes (multi line...)
    show()


def load_n_init(width=64, height=32, bootmsg="micrOS"):
    """
    Init OLED display 64x32 (default)
    Init Neopixel LED (1 segment)
    :param width: screen width (pixel)
    :param height: screen height (pixel)
    :param bootmsg: First text on page at bootup, default: "micrOS"
    """
    neopixel_lni(ledcnt=1)                  #1 Init neopixel
    try:
        oled_lni(width, height)             #2 Init oled display
        _boot_page(bootmsg)                 #3 Show boot page text
        KC.INITED = True                    # Set display was successfully inited (for __task auto init)
        return "OLED INIT OK"
    except Exception as e:
        KC.INITED = False                   # display init failed (for __task auto init)
        return f"OLED INIT NOK: {e}"


def display(period=1000, vd=False):
    """
    Create kc._display task - refresh loop
    :param vd: virtual display 64x32 (rectangle for bigger screens)
    """
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    period_ms = 1000 if period < 1000 else period
    state = micro_task(tag="kc._display", task=__task(period_ms=period_ms, vd=vd))
    return "Starting" if state else "Already running"


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
        state = onoff == 'on'
        return toggle(state, smooth=smooth)
    return 'No action: r g b br onoff smooth'


def press_event():
    """
    IRQ1 keychain module control function
    - neopixel ON/OFF
    - display wake-up (ON)
    """
    # If display is ON call neopixel toggle function
    if KC.DP_main_page:
        # Reset display counter
        KC.DP_cnt = KC.DP_cnt_default
        # Neopixel toggle
        toggle()
        return
    # Wake display
    KC.DP_main_page = True


def lmdep():
    """
    Load Module dependencies
    """
    return 'oled', 'ds18', 'neopixel', 'gameOfLife'


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
    return 'load_n_init width=64 height=32 bootmsg="micrOS"', 'temperature', 'display period>=1000', 'press_event',\
           'neopixel r=<0-255> g=<0-255> b=<0-255> br=<0-100> onoff=<toggle/on/off> smooth=<True/False>',\
           'pinmap', 'lmdep'
