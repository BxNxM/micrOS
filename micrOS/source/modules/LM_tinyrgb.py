import tinypico as TinyPICO
from machine import SoftSPI, Pin
from dotstar import DotStar

# Create a colour wheel index int
COLOR_INDEX = 0
# DOTSTAR POWER, DOTSTAR BRIGHTNESS
DOTSTAR_STATE = [1, 0.5]
DOTSTAR = None


def __init_tinyrgb():
    global DOTSTAR
    if DOTSTAR is None:
        # Configure SPI for controlling the DotStar
        # Internally we are using software SPI for this as the pins being used are not hardware SPI pins
        spi = SoftSPI(sck=Pin(TinyPICO.DOTSTAR_CLK), mosi=Pin(TinyPICO.DOTSTAR_DATA), miso=Pin(TinyPICO.SPI_MISO))
        # Create a DotStar instance
        DOTSTAR = DotStar(spi, 1, brightness=0.5)  # Just one DotStar, half brightness
        # Turn on the power to the DotStar
        TinyPICO.set_dotstar_power(True)
    return DOTSTAR


def setrgb(r=None, g=None, b=None, br=None):
    """
    TinyPico built-in apa102 LED control
    :param r: red value 0-254
    :param g: green value 0-254
    :param b: blue value 0-254
    :param br: brightness of LED 0-100
    """
    __init_tinyrgb()
    r = DOTSTAR[0][0] if r is None else r
    g = DOTSTAR[0][1] if g is None else g
    b = DOTSTAR[0][2] if b is None else b
    DOTSTAR_STATE[1] = DOTSTAR_STATE[1] if br is None else br
    # Get the R,G,B values of the next colour
    DOTSTAR[0] = (r, g, b, DOTSTAR_STATE[1])
    return "RGB: {} ({}%)".format(DOTSTAR, DOTSTAR_STATE[1]*100)


def getstate():
    """
    Get state of TinyPico built-in LED
    """
    return DOTSTAR, DOTSTAR_STATE


def toggle(state=None):
    """
    Toggle TinyPico built-in LED
    :param state bool: True/False/None(default: based on current toggle)
    :return str: verdict
    """
    __init_tinyrgb()
    if state is None:
        state = DOTSTAR_STATE[0]
    # Save state
    DOTSTAR_STATE[0] = 0 if state else 1
    if state:
        TinyPICO.set_dotstar_power(False)
        return "Turn OFF"
    else:
        TinyPICO.set_dotstar_power(True)
        setrgb()
        return "Turn ON"


def wheel(br=None):
    """
    TinyPico ColorWheel generator - step color on LED
    :param br: brightness 0-100
    :return str: verdict
    """
    global COLOR_INDEX
    __init_tinyrgb()
    br = DOTSTAR_STATE[1] if br is None else br
    # Get the R,G,B values of the next colour
    r, g, b = TinyPICO.dotstar_color_wheel(COLOR_INDEX*3)
    # Set the colour on the DOTSTAR
    DOTSTAR[0] = (r, g, b, br)
    # Increase the wheel index
    COLOR_INDEX = 0 if COLOR_INDEX > 500 else COLOR_INDEX + 1
    return "RGB: {}:{}:{} ({}%)".format(r, g, b, DOTSTAR_STATE[1]*100)


#######################
# LM helper functions #
#######################

def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'setrgb r=<0-232> g=<0-232> b=<0-232> br=<0-1>', 'getstate', 'toggle', 'wheel',\
           'NOTE: Available on tinyPICO, used by progressLED'
