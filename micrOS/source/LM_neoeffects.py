from LM_neopixel import load, segment, Data, status, pinmap as pm
from random import randint
from Types import resolve
from Common import manage_task


#################################
#  NEOPIXEL EFFECT DRAWER CLASS #
#################################

class DrawEffect:
    __instance = None

    def __new__(cls, pixcnt=24):
        if DrawEffect.__instance is None:
            DrawEffect.__instance = super().__new__(cls)
            DrawEffect.__instance.pix_cnt = None
            DrawEffect.__instance.index_offset = 0
            DrawEffect.__instance.color_wheel = 0
            DrawEffect.__instance.__init_effect(pixcnt)
            DrawEffect.__instance.offset_gen = None
            DrawEffect.__instance.auto_shift = False
        return DrawEffect.__instance

    def __init_effect(cls, ledcnt):
        """
        Set neopixel object & store pixel cnt
        """
        if Data.NEOPIXEL_OBJ is None:
            load(ledcnt=ledcnt)
            cls.pix_cnt = Data.NEOPIXEL_OBJ.n
        if cls.pix_cnt is None:
            cls.pix_cnt = Data.NEOPIXEL_OBJ.n
        return cls.pix_cnt

    def __offset(cls, shift):
        def _gen():
            while True:
                if cls.auto_shift:
                    # Step rotation cycle - shift True
                    cls.index_offset += 1
                    if cls.index_offset > cls.pix_cnt - 1:
                        cls.index_offset = 0
                for k in range(cls.index_offset, cls.pix_cnt):
                    yield k
                for k in range(0, cls.index_offset):
                    yield k
        cls.auto_shift = shift
        if cls.offset_gen is None:
            cls.offset_gen = _gen()
        return cls.offset_gen

    def draw(cls, iterable, shift=False):
        """
        DRAW GENERATED COLORS (RGB)
        HELPER FUNCTION with auto shift (offset) sub function
        :param iterable: Colors generator object / iterable
        :param shift: automatic color map rotation
        :return: None
        """
        offset_gen = cls.__offset(shift=shift)
        r, g, b, i = 0, 0, 0, 0
        for r, g, b in iterable:
            # Handle index offset - rotate effect
            i = next(offset_gen)
            # Write data to neopixel - write / segment :)
            segment(int(r), int(g), int(b), s=i, cache=False, write=False)
        segment(int(r), int(g), int(b), s=i, cache=False, write=True)
        return True


def __color_input(r, g, b):
    _r, _g, _b, _ = Data.DCACHE
    r = _r if r is None else r
    g = _g if g is None else g
    b = _b if b is None else b
    return r, g, b


#################################
#         DEFINE EFFECTS        #
#################################

def meteor(r=None, g=None, b=None, shift=True, ledcnt=24):
    """
    Meteor effect
    :param r int: red value 0-1000
    :param g int: green value 0-1000
    :param b int: blue value 0-1000
    :param shift bool: automatic effect shifting
    :param ledcnt int: number of neopixel elements in chain (default: 24)
    :return str: verdict
    """
    def __effect(r, g, b, pixel):
        """
        Describe one full length color map
        :param r: red target color
        :param g: green target color
        :param b: blue target color
        :param pixel: number of led segments
        :return: yield tuple with r,g,b
        """
        step = float(0.9 / pixel)
        for k in range(0, pixel):
            fade = (k+1) * step
            data = round(r * fade), round(g * fade), round(b * fade)
            yield data

    # Conditional value load - with neopixel cache
    r, g, b = __color_input(r, g, b)

    # Init custom params
    effect = DrawEffect(pixcnt=ledcnt)
    # Create effect data
    cgen = __effect(r, g, b, effect.pix_cnt)
    # Draw effect data
    effect.draw(cgen, shift=shift)
    return 'Meteor R{}:G{}:B{} N:{}'.format(r, g, b, effect.pix_cnt)


def cycle(r=None, g=None, b=None, shift=True, ledcnt=24):
    """
    Cycle effect
    :param r int: red value 0-1000
    :param g int: green value 0-1000
    :param b int: blue value 0-1000
    :param shift bool: automatic effect shifting
    :param ledcnt int: number of neopixel elements in chain (default: 24)
    :return str: verdict
    """
    def __effect(r, g, b, pixel):
        """
        Describe one full length color map
        :param r: red target color
        :param g: green target color
        :param b: blue target color
        :param pixel: number of led segments
        :return: yield tuple with r,g,b
        """
        lightrgb = round(r*0.1), round(g*0.1), round(b*0.1)
        yield lightrgb
        yield r, g, b
        yield lightrgb
        for i in range(3, pixel):
            yield 0, 0, 0

    # Conditional value load - with neopixel cache
    r, g, b = __color_input(r, g, b)

    effect = DrawEffect(pixcnt=ledcnt)
    cgen = __effect(r, g, b, effect.pix_cnt)
    effect.draw(cgen, shift=shift)
    return 'Cycle R{}:G{}:B{} N:{}'.format(r, g, b, effect.pix_cnt)


def rainbow(step=1, br=50, ledcnt=24):
    """
    Rainbow effect
    :param step int: color weel resolution in step (default: 1)
    :param br int: brightness in percentage
    :param ledcnt int: number of neopixel elements in chain (default: 24)
    :return str: verdict
    """
    def __wheel(pos):
        # Input a value 0 to 255 to get a color value.
        # The colours are a transition r - g - b - back to r.
        if pos < 0 or pos > 255:
            return 0, 0, 0
        if pos < 85:
            return 255 - pos * 3, pos * 3, 0
        if pos < 170:
            pos -= 85
            return 0, 255 - pos * 3, pos * 3
        pos -= 170
        return pos * 3, 0, 255 - pos * 3

    def __effect(cnt, step, br):
        """
        :param cnt: led segment count
        :param br: max brightness 0-100%
        :param step: step size
        """
        cw = DrawEffect().color_wheel
        DrawEffect().color_wheel = 0 if cw >= 255 else cw+step
        for i in range(0, cnt):
            rc_index = (i * 256 // cnt) + DrawEffect().color_wheel
            r, g, b = __wheel(rc_index & 255)
            yield round(r*br*0.01), round(g*br*0.01), round(b*br*0.01)

    effect = DrawEffect(pixcnt=ledcnt)
    cgen = __effect(effect.pix_cnt, step=step, br=br)
    effect.draw(cgen, shift=True)
    return 'Rainbow'


def shader(size=6, offset=0, shift=False, ledcnt=24):
    """
    Shader for ring lamp
    :param size int: shader size (disabled LEDs)
    :param offset int: rotate shader 0-(ledcnt-1)
    :param shift bool: auto shift shader effect (False)
    :param ledcnt int: number of neopixel elements in chain (default: 24)
    :return str: verdict
    """
    def __effect(size, offset, pixcnt):
        # Conditional value load - with neopixel cache
        r, g, b, _ = Data.DCACHE
        # calculate 0->24 range
        _slice1 = pixcnt if size + offset > pixcnt else size + offset
        # calculate 24->0-> range (overflow)
        _slice2 = size + offset - pixcnt if size + offset > pixcnt else 0
        for i in range(0, pixcnt):
            if offset < i < _slice1:
                yield 0, 0, 0
            elif 0 <= i < _slice2:
                yield 0, 0, 0
            else:
                yield r, g, b

    # Init custom params
    effect = DrawEffect(pixcnt=ledcnt)
    # Create effect data
    if size < effect.pix_cnt:
        cgen = __effect(size, offset, effect.pix_cnt)
        # Draw effect data
        effect.index_offset = 0     # reset auto shift offset
        effect.draw(cgen, shift=shift)
        return 'Shader size: {} ->{} ({})'.format(size, offset, effect.pix_cnt)
    return 'Shader invalid size: {} ({})'.format(size, effect.pix_cnt)


def random(max_val=255):
    """
    Demo function: implements random color change
    :param max_val: set channel maximum generated value: 0-255
    :return str: rgb status - states: R, G, B
    """
    r = randint(0, max_val)
    g = randint(0, max_val)
    b = randint(0, max_val)
    Data.DCACHE[0] = r
    Data.DCACHE[1] = g
    Data.DCACHE[2] = b
    return "Set random: R:{} G: B:{}".format(r, g, b)


def color(r=None, g=None, b=None):
    """
    Set color buffer - for runtime effect color change
    :param r int: red channel 0-255 (default: None - cached value)
    :param g int: green channel 0-255 (default: None - cached value)
    :param b int: blue channel 0-255 (default: None - cached value)
    :return dict: rgb status - states: R, G, B, S
    """
    # Conditional value load - with neopixel cache
    r, g, b = __color_input(r, g, b)
    Data.DCACHE[0] = r
    Data.DCACHE[1] = g
    Data.DCACHE[2] = b
    return status()


def fire(r=None, g=None, b=None, ledcnt=24):

    def __effect(r, g, b, pixcnt):
        for _ in range(pixcnt):
            rand_percent = round(randint(1, 200)/100, 2)

            rgb = [
                r * rand_percent,
                g * rand_percent,
                b * rand_percent
            ]

            for i, color in enumerate(rgb):
                if color > 255:
                    rgb[i] = 255
                if color < 0:
                    rgb[i] = 0
            yield rgb

    # Conditional value load - with neopixel cache
    r, g, b = __color_input(r, g, b)

    effect = DrawEffect(pixcnt=ledcnt)
    cgen = __effect(r, g, b, effect.pix_cnt)
    effect.draw(cgen, shift=False)
    return 'fire R{}:G{}:B{} N:{}'.format(r, g, b, effect.pix_cnt)


def stop_effects():
    """
    Stop all running (neo)effects tasks
    """
    return manage_task("neoeffects.*", "kill")

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
    return pm()


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('meteor r=<0-255> g=<0-255> b=<0-255> shift=True ledcnt=24',
                             'BUTTON meteor &&',
                             'cycle r g b shift=True ledcnt=24',
                             'BUTTON cycle &&50',
                             'rainbow step=1 br=<5-100> ledcnt=24 &&',
                             'BUTTON rainbow br=50 &&',
                             'fire r=None g=None b=None ledcnt=24',
                             'BUTTON fire &&200',
                             'BUTTON stop_effects',
                             'shader size=4 offset=0 shift=True ledcnt=24',
                             'random max_val=255',
                             'pinmap',
                             'COLOR color r=<0-255-10> g b'), widgets=widgets)
