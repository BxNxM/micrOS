from LM_neopixel import __init_NEOPIXEL, segment
from LM_neopixel import pinmap as pm


class StateMachine:
    INDEX_OFFSET = 0
    PIX_CNT = None
    COLOR_WHEEL = 0


def __init_effect(ledcnt=24):
    if StateMachine.PIX_CNT is None:
        return __init_NEOPIXEL(n=ledcnt).n
    return StateMachine.PIX_CNT


def __draw(iterable, pixcnt, shift=False):
    """
    DRAW GENERATED COLORS (RGB)
    HELPER FUNCTION with auto shift (offset) sub function
    :param iterable: Colors generator object / iterable
    :ms: wait in ms / step aka speed
    :return: None
    """

    def __offset(pixcnt, shift):
        if shift:
            # Normal rotation cycle
            StateMachine.INDEX_OFFSET += 1
            if StateMachine.INDEX_OFFSET > pixcnt-1:
                StateMachine.INDEX_OFFSET = 0
        for k in range(StateMachine.INDEX_OFFSET, pixcnt):
            yield k
        for k in range(0, StateMachine.INDEX_OFFSET):
            yield k

    # Rotate generator pattern
    i_gen = __offset(pixcnt, shift=shift)
    for r, g, b in iterable:
        i = i_gen.__next__()
        segment(int(r), int(g), int(b), s=i, write=False)
    try:
        # Send (all) and save (last) color
        segment(int(r), int(g), int(b), s=i, cache=True, write=True)
        return True
    except Exception:
        return False


def meteor(r, g, b, shift=False, ledcnt=24):
    def __effect(r, g, b, pixel):
        """
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

    # Init custom params
    pixel_cnt = __init_effect(ledcnt)
    # Create effect data
    cgen = __effect(r, g, b, pixel_cnt)
    # Draw effect data
    __draw(cgen, pixcnt=pixel_cnt, shift=shift)
    return 'Meteor R{}:G{}:B{} N:{}'.format(r, g, b, pixel_cnt)


def cycle(r, g, b, ledcnt=24):
    def __effect(r, g, b, n):
        lightrgb = round(r*0.1), round(g*0.1), round(b*0.1)
        yield lightrgb
        yield r, g, b
        yield lightrgb
        for i in range(3, n):
            yield 0, 0, 0

    cnt = __init_effect(ledcnt)
    data = __effect(r, g, b, cnt)
    cgen = __draw(data, pixcnt=cnt, shift=True)
    return 'Cycle: {}'.format(cgen)


def rainbow(step=15, br=100, ledcnt=24):
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
        cw = StateMachine.COLOR_WHEEL
        StateMachine.COLOR_WHEEL = 0 if cw >= 255 else cw+step
        for i in range(0, cnt):
            rc_index = (i * 256 // cnt) + StateMachine.COLOR_WHEEL
            r, g, b = __wheel(rc_index & 255)
            yield round(r*br*0.01), round(g*br*0.01), round(b*br*0.01)

    cnt = __init_effect(ledcnt)
    gen = __effect(cnt, step=step, br=br)
    o = __draw(gen, pixcnt=cnt, shift=True)
    return 'Rainbow: {}'.format(o)


#######################
# LM helper functions #
#######################

def lmdep():
    return 'neopixel'


def pinmap():
    return pm()


def help():
    return 'meteor r=<0-255> g=<0-255> b=<0-255> shift=False ledcnt=24',\
           'cycle r g b ledcnt=24', 'rainbow step=15 br=<5-100> ledcnt=24', 'pinmap'
