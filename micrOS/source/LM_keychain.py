from utime import localtime, sleep_ms
from neopixel import NeoPixel
from machine import Pin
from Common import micro_task
from microIO import bind_pin, pinmap_search
from LM_oled import text, show, rect, pixel, clean, line, load as oled_lni
from LM_ds18 import measure
from LM_system import top, ifconfig
try:
    from LM_gameOfLife import next_gen as gol_nextgen, reset as gol_reset
except:
    gol_nextgen = None      # Optional function handling

class KC:
    INITED = False          # Auto init module feature
    DP_main_page = True     # store display logical state: ON (main page) / OFF (screen saver)
    DP_cnt = 0              # display "count back", when 0 go to sleep -> OFF
    DP_cnt_default = None   # store calculated sequence to sleep 30sec/period_ms
    NEOPIXEL_OBJ = None     # Neopixel LED handler object
    COLOR_WHEEL = None      # LED color wheel generator object for animation
    NEOPIXEL_BR = 20        # default neopixel brightness

#############################
#    INTERNAL FUNCTIONS     #
#############################


async def _screen_saver(scale=2):
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
        # quick view - show (enable) main page
        KC.DP_main_page = True
    else:
        # Update display with Conway's Game of Life
        clean()
        for line_idx, _line in enumerate(matrix):
            for x_idx, v in enumerate(_line):
                if scale == 1:
                    pixel(x_idx, line_idx, color=v)
                else:
                    rect(x_idx*scale, line_idx*scale, w=scale, h=scale, state=v, fill=True)
        show()


def __color_wheel():
    """
    RGB LED color wheel generator - rainbow
    """
    max_val = 10                    # normally up to 255, but must be limited due to heat problems (4%)
    half_val = max_val // 2
    colors = ((0, 0, half_val), (0, 0, max_val), (0, half_val, max_val), (0, max_val, half_val), (0, max_val, 0),
              (half_val, max_val, 0), (max_val, half_val, 0), (max_val, 0, 0), (half_val, 0, 0), (max_val, 0, half_val),
              (half_val, 0, max_val), (0, 0, half_val))
    while True:
        # Loop through the colors to generate smooth transitions
        for i in range(len(colors) - 1):
            start_color = colors[i]
            end_color = colors[i + 1]
            # Generate a smooth transition from start_color to end_color
            for j in range(5):  # Adjust this value for smoother or faster transition
                # Linear interpolation for each color component
                yield tuple(int(start + (end - start) * j / 10) for start, end in zip(start_color, end_color))


async def _main_page():
    """
    Run display content refresh
        #   H:M
         S/A: 1.92
         40.0 C
    """
    def _timer():
        # 5x5 px cube (25px overall)
        _offset, _l_width = 2, 5                                # Initial size + positioning
        _view = int(25*(KC.DP_cnt/KC.DP_cnt_default))           # overall pixel to be visualized
        _complete_lines = int(_view / _l_width)                 # complete lines number
        _sub_line = _view - (_complete_lines*_l_width)          # incomplete line width
        for _l in range(0, 5):
            if _l < _complete_lines:
                line(0+_offset, _l+_offset, _l_width+_offset, _l+_offset)
            else:
                line(0+_offset, _l+_offset, _sub_line+_offset, _l+_offset)
                break

    def _cpu_mem():
        sys_usage = top()
        cpu = sys_usage.get('CPU load [%]', 100)
        cpu = 100 if cpu > 100 else cpu                                             # limit cpu overload in visualization
        mem = sys_usage.get('Mem usage [%]', 100)
        _cpu_limit, _mem_limit = cpu > 90, mem > 70                                 # fill indicator (limit)
        _offset, _height = 1, 6
        _cpu, _mem = int(_height * (cpu/100)), int(_height * (mem/100))
        rect(55, _height+_offset-_cpu, w=3, h=_cpu+_offset, fill=_cpu_limit)     # cpu usage indicator
        rect(60, _height+_offset-_mem, w=3, h=_mem+_offset, fill=_mem_limit)     # memory usage indicator

    # Clean display and collect input data: time, network mode, IP address
    clean()
    ltime = localtime()
    h = f"0{ltime[-5]}" if len(str(ltime[-5])) < 2 else ltime[-5]
    m = f"0{ltime[-4]}" if len(str(ltime[-4])) < 2 else ltime[-4]
    nwmd, nwif = ifconfig()
    nwmd, devip = nwmd[0] if len(nwmd) > 0 else "0", ".".join(nwif[0].split(".")[-2:])

    # Draw data to display
    _timer()                                                                    # Draw display timer (until screen saver)
    _cpu_mem()                                                                  # Draw cpu and memory indicator
    text(f"{h}:{m}", x=12, y=1)                                           # Header: time
    text(f"{nwmd}:{devip}", x=4, y=15)                                    # Network mode and IP
    try:
        text(f"{round(tuple(measure().values())[0], 1)} C", x=4, y=25)    # ds18 sensor value
    except Exception:
        text("? C", x=4, y=25)                                            # ds18 read issue (default: ?)
    show()
    return "Display show"


async def _ui_task(period_ms, tts_ms):
    """Async display refresh task
    - main page    (main mode)
    - screen saver (sleep mode)
    """
    # Auto init keychain module (if needed) - failsafe
    if not KC.INITED:
        _v = load()
        if not KC.INITED:
            return _v

    KC.DP_cnt_default = int(tts_ms / period_ms)     # After 30 sec go to sleep mode
    KC.DP_cnt = KC.DP_cnt_default                   # Set sleep counter
    fast_period = int(period_ms/3)                  # Calculate faster refresh period
    fast_period = fast_period if fast_period > 100 else 100

    # Run keychain main async loop, with update ID: keychain.display
    with micro_task(tag="keychain.display") as my_task:
        while True:
            if KC.DP_main_page:
                # [MAIN MODE] Execute main page
                await _main_page()                          #1 Run main page function
                my_task.out = f'main page: {KC.DP_cnt}'     #2 Update task data for (task show keychain.display)
                KC.DP_cnt -= 1                              #3 Update sleep counter
                # Async sleep - feed event loop
                await my_task.feed(sleep_ms=period_ms)
            else:
                # [SLEEP MODE] Execute screen saver page
                await _screen_saver()                       # Run sleep page function
                # Async sleep - feed event loop
                await my_task.feed(sleep_ms=fast_period)

            # Auto sleep event handler - off event - go to (sleep mode)
            if KC.DP_cnt <= 0:
                KC.DP_main_page = False         #1 disable main screen
                clean()                         #2 clean screen
                show()                          #3 show cleaned display
                KC.DP_cnt = KC.DP_cnt_default   #4 reset sleep counter to default
                my_task.out = 'sleep...'
            color_wheel()              # update neopixel color wheel


#############################
#      PUBLIC FUNCTIONS     #
#############################

def load(width=64, height=32, bootmsg="micrOS"):
    """
    Init OLED display 64x32 (default)
    Init Neopixel LED (1 segment)
    :param width: screen width (pixel)
    :param height: screen height (pixel)
    :param bootmsg: First text on page at bootup, default: "micrOS"
    """
    KC.COLOR_WHEEL = __color_wheel()            #1 Init neopixel color wheel generator
    try:
        oled_lni(width, height, brightness=20)  #2 Init oled display
        msgbox(bootmsg, width)                  #3 Show boot page text
        KC.INITED = True                        # Set display was successfully inited (for _task auto init)
        return "OLED INIT OK"
    except Exception as e:
        KC.INITED = False                       # display init failed (for _task auto init)
        return f"OLED INIT NOK: {e}"


def msgbox(msg, width=64):
    clean()
    chunk_size, char_height, line_limit = 8, 10, 3
    # Format message: fitting and \n parsing
    msg = msg.split('\n')
    chunks = [line[i:i + chunk_size] for line in msg for i in range(0, len(line), chunk_size)]
    for i, line in enumerate(chunks):
        if i > line_limit - 1:  # max line_limit lines of 13 char
            break
        start_x = int((width - len(line)*8)/2)
        start_y = char_height * i
        for k in range(0, len(line)):
            text(line[0:k+1], start_x, start_y)
            show()
            sleep_ms(100)
    sleep_ms(2000)


def display(period=1000, tts=30):
    """
    Create keychain.display task - refresh loop
    :param period: display refresh period in ms (min. 500ms)
    :param tts: time to sleep (in seconds)
    """
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    period_ms = 500 if period < 500 else period
    tts_ms = 5000 if tts < 5 else tts*1000
    state = micro_task(tag="keychain.display", task=_ui_task(period_ms, tts_ms))
    return "Starting" if state else "Already running"


def temperature():
    """
    Measure ds18B20 temperature sensor
    """
    return measure()


def color_wheel(br=None):
    """
    Neopixel color wheel
    :param br: brightness value 0-100 percent
    """
    def _init():
        if KC.NEOPIXEL_OBJ is None:
            neopixel_pin = Pin(bind_pin('neop'))        # Get Neopixel pin from LED PIN pool
            KC.NEOPIXEL_OBJ = NeoPixel(neopixel_pin, n=1)   # initialize for max 1 segment
        return KC.NEOPIXEL_OBJ
    # INIT
    neo_led = _init()
    if br is None or not isinstance(br, int):       # Optional brightness param handling (load from cache)
        br = KC.NEOPIXEL_BR
    else:
        KC.NEOPIXEL_BR = br                         # update neopixel brightness cache
    if KC.COLOR_WHEEL is None:
        KC.COLOR_WHEEL = __color_wheel()             # init color wheel generator
    # UPDATE
    r, g, b = next(KC.COLOR_WHEEL)                  # get next color
    br = br if br == 100 else br/100                # calculate brightness multiplier
    r, g, b = int(r*br), int(g*br), int(b*br)       # apply brightness parameter
    neo_led[0] = (r, g, b)                          # Set LED element color
    neo_led.write()                                 # Send data to LED device
    return {'R': r, 'G': g, 'B': b, 'S': 1, 'br': br}   # Return verdict


def display_toggle():
    """
    Display mode toggle (main/screensaver)
    """
    KC.DP_main_page = not KC.DP_main_page
    if not KC.DP_main_page:
        # Reset display counter when goes to sleep
        KC.DP_cnt = KC.DP_cnt_default
    v = 'main view' if KC.DP_main_page else 'screensaver'
    return f"Display mode: {v}"


def neopixel_toggle():
    """
    Disable/Enable neopixel LED (brightness 0/default)
    """
    KC.NEOPIXEL_BR = 0 if KC.NEOPIXEL_BR > 0 else 20
    v = 'disabled' if KC.NEOPIXEL_BR == 0 else 'enabled'
    return f"Neopixel: {v} br: {KC.NEOPIXEL_BR}"


def button():
    """
    IRQ1 keychain module control function
    - neopixel ON/OFF
    - display wake-up (ON)
    """
    # If display is ON call neopixel toggle function
    if KC.DP_main_page:
        # Reset display counter
        KC.DP_cnt = KC.DP_cnt_default
        # Neopixel color wheel disable/enable
        return neopixel_toggle()
    # Wake display
    KC.DP_main_page = True
    return "Display mode: main view"


def pinmap():
    """
    PIN MAP dump
    """
    from LM_oled import pinmap as o_pmp
    from LM_ds18 import pinmap as t_pmp
    pmp = o_pmp()
    pmp.update(t_pmp())
    pmp.update(pinmap_search(['neop']))
    return pmp


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return ('load width=64 height=32 bootmsg="micrOS"',
            'msgbox msg="micrOS"',
            'temperature', 
            'display period>=1000 tts=30',
            'button',
            'display_toggle',
            'neopixel_toggle',
            'color_wheel br=<0-100>',
            'pinmap')
