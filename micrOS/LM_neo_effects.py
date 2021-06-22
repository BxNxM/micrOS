from LM_neopixel import __init_NEOPIXEL, segment


class StateMachine:
    INDEX_OFFSET = 0
    REV_OFFSET = False
    COLOR_WHEEL = 0


def __draw(iterable, shift=False, back=False):
    """
    DRAW GENERATED COLORS (RGB)
    HELPER FUNCTION with auto shift (offset) sub function
    :param iterable: Colors generator object / iterable
    :ms: wait in ms / step aka speed
    :return: None
    """

    def __offset(itr, back=False, pixcnt=24):
        pos = StateMachine.INDEX_OFFSET
        if StateMachine.REV_OFFSET:
            if StateMachine.INDEX_OFFSET > 1:
                StateMachine.INDEX_OFFSET = pos - 1
            elif back:
                StateMachine.REV_OFFSET = False
                StateMachine.INDEX_OFFSET = 1
            else:
                StateMachine.INDEX_OFFSET = pixcnt-1
            return tuple(itr[pos:pixcnt] + itr[0:pos])
        if StateMachine.INDEX_OFFSET < pixcnt:
            StateMachine.INDEX_OFFSET = pos + 1
        elif back:
            StateMachine.REV_OFFSET = True
            StateMachine.INDEX_OFFSET = pixcnt-1
        else:
            StateMachine.INDEX_OFFSET = 0
        return tuple(itr[pos:pixcnt] + itr[0:pos])

    if shift:
        # Rotate generator pattern
        iterable = __offset(iterable, back, pixcnt=len(iterable))
    for i, c in enumerate(iterable):
        # Get colors for pixels
        r, g, b = c
        segment(int(r), int(g), int(b), s=i, write=False)
    try:
        # Send (all) and save (last) color(s)
        segment(int(r), int(g), int(b), s=i, cache=True, write=True)
        return True
    except Exception:
        return False


def meteor(r, g, b, shift=False, back=False, ledcnt=24):
    def __effect(r, g, b, pixel_cnt, fade_step):
        """
        :param r: red target color
        :param g: green target color
        :param b: blue target color
        :param pixel_cnt: number of led segments
        :param fade_step: fade unit
        :return: yield tuple with r,g,b "return"
        """
        data = []
        for k in range(0, pixel_cnt):
            fade_multi = (k+1) * fade_step
            buff = int(r * fade_multi), int(g * fade_multi), int(b * fade_multi)
            data.append(buff)
        return data
    # Init custom params
    pixel_cnt = __init_NEOPIXEL(n=ledcnt).n
    fade_step = float(1.0 / pixel_cnt)
    # Create effect data
    cdata = __effect(r, g, b, pixel_cnt, fade_step)
    # Draw effect data
    __draw(cdata, shift=shift, back=back)
    return 'Meteor R{}:G{}:B{} N:{}'.format(r, g, b, pixel_cnt)


def rainbow(step=1, ledcnt=24):
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

    def __effect(cnt, step):
        """
        :param cnt: led segment count
        :param maxbr: max brightness 0-255
        :param step: step size
        """
        cw = StateMachine.COLOR_WHEEL
        StateMachine.COLOR_WHEEL = 0 if cw >= 255 else cw+step
        for i in range(0, cnt):
            rc_index = (i * 256 // cnt) + StateMachine.COLOR_WHEEL
            yield __wheel(rc_index & 255)

    cnt = __init_NEOPIXEL(n=ledcnt).n
    gen = __effect(cnt, step=step)
    o = __draw(gen)
    return 'Rainbow: {}'.format(o)


def cycle(r, g, b, bounce=False, ledcnt=24):
    def __effect(r, g, b, n):
        data = [(r, g, b)]
        for i in range(1, n):
            data.append((0, 0, 0))
        return data

    cnt = __init_NEOPIXEL(n=ledcnt).n
    data = __effect(r, g, b, cnt)
    o = __draw(data, shift=True, back=bounce)
    return 'Cycle: {}'.format(o)


def lmdep():
    return 'LM_neopixel'


def help():
    return 'meteor r=<0-255> g=<0-255> b=<0-255> shift=False back=False ledcnt=24',\
           'rainbow step=1 ledcnt=24', 'cycle r g b bounce=False ledcnt'
