import tinypico as TinyPICO
from machine import SoftSPI, Pin
from dotstar import DotStar

# Create a colour wheel index int
COLOR_INDEX = 0
DOTSTAR = None


def init_APA102():
    global DOTSTAR
    # Configure SPI for controlling the DotStar
    # Internally we are using software SPI for this as the pins being used are not hardware SPI pins
    spi = SoftSPI(sck=Pin(TinyPICO.DOTSTAR_CLK), mosi=Pin(TinyPICO.DOTSTAR_DATA), miso=Pin(TinyPICO.SPI_MISO))
    # Create a DotStar instance
    DOTSTAR = DotStar(spi, 1, brightness=0.4)  # Just one DotStar, half brightness
    # Turn on the power to the DotStar
    TinyPICO.set_dotstar_power(True)
    return True


def step():
    global COLOR_INDEX, DOTSTAR
    # Get the R,G,B values of the next colour
    r, g, b = TinyPICO.dotstar_color_wheel(COLOR_INDEX*2)
    # Set the colour on the DOTSTAR
    DOTSTAR[0] = (int(r*0.6), g, b, 0.4)
    # Increase the wheel index
    COLOR_INDEX = 0 if COLOR_INDEX > 1000 else COLOR_INDEX+2
