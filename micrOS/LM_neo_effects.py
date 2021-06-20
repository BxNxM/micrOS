from LM_neopixel import __init_NEOPIXEL, segment

INDEX_OFFSET = 0


def __draw(gen_obj, shift=False):
    """
    DRAW GENERATED COLORS (RGB)
    HELPER FUNCTION with auto shift (offset) sub function
    :param gen_obj: Colors generator object / iterable
    :ms: wait in ms / step aka speed
    :return: None
    """
    def __offset(iterable):
        global INDEX_OFFSET
        pixel_cnt = __init_NEOPIXEL().n
        pos = INDEX_OFFSET
        buffer = [(0, 0, 0) for _ in range(0, pixel_cnt)]
        for k in range(pos, pixel_cnt):
            buffer[k] = iterable.__next__()
        for k in range(0, pos):
            buffer[k] = iterable.__next__()
        INDEX_OFFSET = pos + 1 if INDEX_OFFSET < pixel_cnt else 0
        return tuple(buffer)

    r, g, b, i = 0, 0, 0, 0
    if shift:
        # Rotate generator pattern
        gen_obj = __offset(gen_obj)
    for i, c in enumerate(gen_obj):
        # Get colors for pixels
        r, g, b = c
        segment(int(r), int(g), int(b), s=i, write=False)
    # Send (all) and save (last) color(s)
    segment(int(r), int(g), int(b), s=i, cache=True, write=True)


def meteor(r, g, b, shift=False, ledcnt=24):
    def __effect(r, g, b, pixel_cnt, fade_step):
        """
        :param r: red target color
        :param g: green target color
        :param b: blue target color
        :param pixel_cnt: number of led segments
        :param fade_step: fade unit
        :return: yield tuple with r,g,b "return"
        """
        for k in range(0, pixel_cnt):
            fade_multi = (k+1) * fade_step
            yield int(r * fade_multi), int(g * fade_multi), int(b * fade_multi)
    # Init custom params
    pixel_cnt = __init_NEOPIXEL(n=ledcnt).n
    fade_step = float(1.0 / pixel_cnt)
    # Construct generator object
    g = __effect(r, g, b, pixel_cnt, fade_step)
    # Draw generator obj
    __draw(g, shift=shift)
    return 'Meteor R{}:G{}:B{} N:{}'.format(r, g, b, pixel_cnt)


def lmdep():
    return 'LM_neopixel'


def help():
    return 'meteor r=<0-255> g=<0-255> b=<0-255> shift=False'
