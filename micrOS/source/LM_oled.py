# MicroPython SSD1306 OLED driver, I2C and SPI interfaces

from micropython import const
import framebuf
from machine import Pin, SoftI2C
from microIO import bind_pin, pinmap_search
from Types import resolve

__INVERT = False


###################################
#   SSD1306 class implementation  #
###################################

# register definitions
SET_CONTRAST = const(0x81)
SET_ENTIRE_ON = const(0xA4)
SET_NORM_INV = const(0xA6)
SET_DISP = const(0xAE)
SET_MEM_ADDR = const(0x20)
SET_COL_ADDR = const(0x21)
SET_PAGE_ADDR = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP = const(0xA0)
SET_MUX_RATIO = const(0xA8)
SET_IREF_SELECT = const(0xAD)
SET_COM_OUT_DIR = const(0xC0)
SET_DISP_OFFSET = const(0xD3)
SET_COM_PIN_CFG = const(0xDA)
SET_DISP_CLK_DIV = const(0xD5)
SET_PRECHARGE = const(0xD9)
SET_VCOM_DESEL = const(0xDB)
SET_CHARGE_PUMP = const(0x8D)


# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class SSD1306(framebuf.FrameBuffer):

    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP,  # display off
            # address setting
            SET_MEM_ADDR,
            0x00,  # horizontal
            # resolution and layout
            SET_DISP_START_LINE,  # start at line 0
            SET_SEG_REMAP | 0x01,  # column addr 127 mapped to SEG0
            SET_MUX_RATIO,
            self.height - 1,
            SET_COM_OUT_DIR | 0x08,  # scan from COM[N] to COM0
            SET_DISP_OFFSET,
            0x00,
            SET_COM_PIN_CFG,
            0x02 if self.width > 2 * self.height else 0x12,
            # timing and driving scheme
            SET_DISP_CLK_DIV,
            0x80,
            SET_PRECHARGE,
            0x22 if self.external_vcc else 0xF1,
            SET_VCOM_DESEL,
            0x30,  # 0.83*Vcc
            # display
            SET_CONTRAST,
            0xFF,  # maximum
            SET_ENTIRE_ON,  # output follows RAM contents
            SET_NORM_INV,  # not inverted
            SET_IREF_SELECT,
            0x30,  # enable internal IREF during display on
            # charge pump
            SET_CHARGE_PUMP,
            0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01,  # display on
        ):  # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()

    def poweroff(self):
        self.write_cmd(SET_DISP)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)

    def contrast(self, percent):
        """percent: 0-100"""
        contrast = int(255*(percent/100))
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def rotate(self, rotate):
        self.write_cmd(SET_COM_OUT_DIR | ((rotate & 1) << 3))
        self.write_cmd(SET_SEG_REMAP | (rotate & 1))

    def image(self, pbm_file, x=0, y=0):
        # Load Portable Bitmap Format (PBM) formatted image from file
        with open(pbm_file, 'rb') as f:
            f.readline()  # Magic number
            f.readline()  # Creator comment
            f.readline()  # Dimensions
            data = bytearray(f.read())
        fbuf = framebuf.FrameBuffer(data, self.width, self.height, framebuf.MONO_HLSB)
        self.invert(1)          # Clear display
        self.blit(fbuf, x, y)

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width != 128:
            # narrow displays use centred columns
            col_offset = (128 - self.width) // 2
            x0 += col_offset
            x1 += col_offset
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)


class SSD1306_I2C(SSD1306):
    OLED_OBJ = None

    def __init__(self, width, height, i2c, addr=0x3C, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b"\x40", None]  # Co=0, D/C#=1
        super().__init__(width, height, external_vcc)
        SSD1306_I2C.OLED_OBJ = self

    def write_cmd(self, cmd):
        self.temp[0] = 0x80  # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)


###################################
#  SSD1306 interface functions    #
###################################

def load(width=128, height=64, brightness=50):
    """
    :param width: pixel
    :param height: pixel
    :param brightness: percentage
    """
    if SSD1306_I2C.OLED_OBJ is None:
        i2c = SoftI2C(Pin(bind_pin('i2c_scl')), Pin(bind_pin('i2c_sda')))
        # TODO: scan device - abort if no device is available
        SSD1306_I2C.OLED_OBJ = SSD1306_I2C(width, height, i2c)
        SSD1306_I2C.OLED_OBJ.contrast(percent=brightness)
    return SSD1306_I2C.OLED_OBJ


def text(string="text", x=0, y=0):
    """
    Create text on OLED
    :param string: text to draw
    :param x: 0-127
    :param y: 0-63
    """
    load().text(string, x, y)
    return True


def invert():
    """
    Invert OLED display
    """
    global __INVERT
    load()
    __INVERT = not __INVERT
    SSD1306_I2C.OLED_OBJ.invert(__INVERT)
    return True


def clean(state=0):
    """
    Clean display
    :param state: 0/1
    """
    load().fill(state)
    return True


def line(sx, sy, ex, ey, state=1):
    """
    Draw line on OLED
    :param sx: start x
    :param sy: start y
    :param ex: end x
    :param ey: end y
    :param state: state 0/1
    """
    load().line(sx, sy, ex, ey, state)
    return True


def rect(x, y, w, h, state=1, fill=False):
    """
    Draw rectangle on OLED
    :param x: start x
    :param y: start y
    :param w: width
    :param h: height
    :param state: state
    :param fill: fill rectangle (True/False)
    """
    if fill:
        load().fill_rect(x, y, w, h, state)
    else:
        load().rect(x, y, w, h, state)
    return True

def pixel(x, y, color=1):
    """
    https://blog.martinfitzpatrick.com/oled-displays-i2c-micropython/
    Set pixel
    .pixel(x, y, c)
    """
    load().pixel(x, y, color)  # 3rd param is the colour
    return True


def bitmap(bmp=None, x=0, y=0):
    """
    Draw simple bitmap
    :param bmp: lines of image string ('001','011','111')
    :param x: x offset
    :param y: y offset
    """
    if bmp is None:
        """default bmp 14x14:
                # #    # #
                # #    # # 
            # # # # # # # # # #
            # # # # # # # # # #
        # # # #             # # # #
        # # # #             # # # #
            # #     # #     # #
            # #     # #     # #
        # # # #             # # # #
        # # # #             # # # #
            # # # # # # # # # #
            # # # # # # # # # #
                # #     # #
                # #     # #
        """
        bmp = ('00001100110000',
               '00001100110000',
               '11111111111111',
               '11111111111111',
               '11110000001111',
               '11110000001111',
               '00110011001100',
               '00110011001100',
               '11110000001111',
               '11110000001111',
               '11111111111111',
               '11111111111111',
               '00001100110000',
               '00001100110000')

    display = load()
    for _y, row in enumerate(bmp):
        for _x, c in enumerate(row):
            display.pixel(_x+x, _y+y, int(c))
    return True


def image(pbm_img, x=0, y=0):
    """
    [BETA]
    https://blog.martinfitzpatrick.com/displaying-images-oled-displays/
    Load Portable Bitmap Format (PBM) image
    :param pbm_img: .pbm image path
    :param x: x offset
    :param y: y offset
    """
    load().image(pbm_file=pbm_img, x=x, y=y)
    return True



def poweron():
    """
    Power ON OLED
    """
    load().poweron()
    return True


def poweroff():
    """
    Power OFF OLED
    """
    load().poweroff()
    return True


def show():
    """
    Show OLED buffer data
    - update display
    """
    SSD1306_I2C.OLED_OBJ.show()


#######################
# LM helper functions #
#######################

def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_search(['i2c_scl', 'i2c_sda'])


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('load width=128 height=64',
                             'text "text" x y',
                             'BUTTON invert',
                             'clean state=<0/1>',
                             'line sx sy ex ey state=1',
                             'rect x y w h state=1 fill=False',
                             'pixel x y color=1',
                             'bitmap bmp=<str tuple> x=0 y=0',
                             'image pbm_img x=0 y=0',
                             'show', 'BUTTON poweron', 'BUTTON poweroff',
                             'pinmap', '[Info] OLED Module for SSD1306'), widgets=widgets)

