# https://github.com/robert-hh/SH1106
#
# Pin's for I2C can be set almost arbitrary
#
# from machine import Pin, I2C
# import sh1106
#
# i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
# display = sh1106.SH1106_I2C(128, 64, i2c, Pin(16), 0x3c)
# display.sleep(False)
# display.fill(0)
# display.text('Testing 1', 0, 0, 1)
# display.show()

from micropython import const
import utime as time
import framebuf
from machine import Pin, I2C
from microIO import bind_pin, pinmap_search
from Types import resolve

__INVERT = False

###################################
#   SH1106 class implementation   #
###################################

# a few register definitions
_SET_CONTRAST        = const(0x81)
_SET_NORM_INV        = const(0xa6)
_SET_DISP            = const(0xae)
_SET_SCAN_DIR        = const(0xc0)
_SET_SEG_REMAP       = const(0xa0)
_LOW_COLUMN_ADDRESS  = const(0x00)
_HIGH_COLUMN_ADDRESS = const(0x10)
_SET_PAGE_ADDRESS    = const(0xB0)


class SH1106(framebuf.FrameBuffer):

    def __init__(self, width, height, external_vcc, rotate=0):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.flip_en = rotate == 180 or rotate == 270
        self.rotate90 = rotate == 90 or rotate == 270
        self.pages = self.height // 8
        self.bufsize = self.pages * self.width
        self.renderbuf = bytearray(self.bufsize)
        self.pages_to_update = 0

        if self.rotate90:
            self.displaybuf = bytearray(self.bufsize)
            # HMSB is required to keep the bit order in the render buffer
            # compatible with byte-for-byte remapping to the display buffer,
            # which is in VLSB. Else we'd have to copy bit-by-bit!
            super().__init__(self.renderbuf, self.height, self.width,
                             framebuf.MONO_HMSB)
        else:
            self.displaybuf = self.renderbuf
            super().__init__(self.renderbuf, self.width, self.height,
                             framebuf.MONO_VLSB)

        # flip() was called rotate() once, provide backwards compatibility.
        self.rotate = self.flip
        self.init_display()

    def init_display(self):
        self.reset()
        self.fill(0)
        self.show()
        self.poweron()
        # rotate90 requires a call to flip() for setting up.
        self.flip(self.flip_en)

    def poweroff(self):
        self.write_cmd(_SET_DISP | 0x00)

    def poweron(self):
        self.write_cmd(_SET_DISP | 0x01)
        if self.delay:
            time.sleep_ms(self.delay)

    def flip(self, flag=None, update=True):
        if flag is None:
            flag = not self.flip_en
        mir_v = flag ^ self.rotate90
        mir_h = flag
        self.write_cmd(_SET_SEG_REMAP | (0x01 if mir_v else 0x00))
        self.write_cmd(_SET_SCAN_DIR | (0x08 if mir_h else 0x00))
        self.flip_en = flag
        if update:
            self.show(True) # full update

    def sleep(self, value):
        self.write_cmd(_SET_DISP | (not value))

    def contrast(self, percent):
        """percent: 0-100"""
        contrast = int(255 * (percent / 100))
        self.write_cmd(_SET_CONTRAST)
        self.write_cmd(contrast)

    def invert(self, invert):
        self.write_cmd(_SET_NORM_INV | (invert & 1))

    def show(self, full_update = False):
        # self.* lookups in loops take significant time (~4fps).
        (w, p, db, rb) = (self.width, self.pages,
                          self.displaybuf, self.renderbuf)
        if self.rotate90:
            for i in range(self.bufsize):
                db[w * (i % p) + (i // p)] = rb[i]
        if full_update:
            pages_to_update = (1 << self.pages) - 1
        else:
            pages_to_update = self.pages_to_update
        #print("Updating pages: {:08b}".format(pages_to_update))
        for page in range(self.pages):
            if (pages_to_update & (1 << page)):
                self.write_cmd(_SET_PAGE_ADDRESS | page)
                self.write_cmd(_LOW_COLUMN_ADDRESS | 2)
                self.write_cmd(_HIGH_COLUMN_ADDRESS | 0)
                self.write_data(db[(w*page):(w*page+w)])
        self.pages_to_update = 0

    def pixel(self, x, y, color=None):
        if color is None:
            return super().pixel(x, y)
        else:
            super().pixel(x, y, color)
            page = y // 8
            self.pages_to_update |= 1 << page

    def text(self, text, x, y, color=1):
        super().text(text, x, y, color)
        self.register_updates(y, y+7)

    def line(self, x0, y0, x1, y1, color):
        super().line(x0, y0, x1, y1, color)
        self.register_updates(y0, y1)

    def hline(self, x, y, w, color):
        super().hline(x, y, w, color)
        self.register_updates(y)

    def vline(self, x, y, h, color):
        super().vline(x, y, h, color)
        self.register_updates(y, y+h-1)

    def fill(self, color):
        super().fill(color)
        self.pages_to_update = (1 << self.pages) - 1

    def blit(self, fbuf, x, y, key=-1, palette=None):
        super().blit(fbuf, x, y, key, palette)
        self.register_updates(y, y+self.height)

    def scroll(self, x, y):
        # my understanding is that scroll() does a full screen change
        super().scroll(x, y)
        self.pages_to_update =  (1 << self.pages) - 1

    def fill_rect(self, x, y, w, h, color):
        super().fill_rect(x, y, w, h, color)
        self.register_updates(y, y+h-1)

    def rect(self, x, y, w, h, color):
        super().rect(x, y, w, h, color)
        self.register_updates(y, y+h-1)

    def register_updates(self, y0, y1=None):
        # this function takes the top and optional bottom address of the changes made
        # and updates the pages_to_change list with any changed pages
        # that are not yet on the list
        start_page = max(0, y0 // 8)
        end_page = max(0, y1 // 8) if y1 is not None else start_page
        # rearrange start_page and end_page if coordinates were given from bottom to top
        if start_page > end_page:
            start_page, end_page = end_page, start_page
        for page in range(start_page, end_page+1):
            self.pages_to_update |= 1 << page

    def reset(self, res=None):
        if res is not None:
            res(1)
            time.sleep_ms(1)
            res(0)
            time.sleep_ms(20)
            res(1)
            time.sleep_ms(20)


class SH1106_I2C(SH1106):
    OLED_OBJ = None

    def __init__(self, width, height, i2c, res=None, addr=0x3c,
                 rotate=0, external_vcc=False, delay=0):
        self.i2c = i2c
        self.addr = addr
        self.res = res
        self.temp = bytearray(2)
        self.delay = delay
        if res is not None:
            res.init(res.OUT, value=1)
        super().__init__(width, height, external_vcc, rotate)
        SH1106_I2C.OLED_OBJ = self

    def write_cmd(self, cmd):
        self.temp[0] = 0x80  # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.i2c.writeto(self.addr, b'\x40'+buf)

    def reset(self):
        super().reset(self.res)


###################################
#   SH1106 interface functions    #
###################################

def load(width=128, height=64, brightness=50, rotate=180):
    if SH1106_I2C.OLED_OBJ is None:
        #i2c = SoftI2C(Pin(bind_pin('i2c_scl')), Pin(bind_pin('i2c_sda')))
        i2c = I2C(scl=Pin(bind_pin('i2c_scl')), sda=Pin(bind_pin('i2c_sda')), freq=400000)
        # TODO: scan device - abort if no device is available
        SH1106_I2C.OLED_OBJ = SH1106_I2C(width, height, i2c, rotate=rotate)
        SH1106_I2C.OLED_OBJ.contrast(percent=brightness)
    return SH1106_I2C.OLED_OBJ


def text(string="text", x=0, y=0):
    """
    Create text on OLED
    :param string: text to draw
    :param x: 0-127
    :param y: 0-63
    """
    load().text(string, x, y, color=1)
    return True


def invert():
    """
    Invert OLED display
    """
    global __INVERT
    load()
    __INVERT = not __INVERT
    load().invert(invert=__INVERT)
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


def pixel(x, y, state=1):
    load().pixel(x, y, color=state)
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
    load().show()


def flip():
    load().flip()
    return True


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
    return resolve(('load width=128 height=64 rotate=180',
                             'text "text" x y',
                             'BUTTON invert', 'clean state=<0/1>',
                             'line sx sy ex ey state=1',
                             'rect x y w h state=1 fill=False',
                             'pixel x y state', 'bitmap bmp=None x=0 y=0',
                             'show', 'BUTTON poweron', 'BUTTON poweroff',
                             'flip', 'pinmap',
                             '[Info] OLED Module for SH1106'), widgets=widgets)

