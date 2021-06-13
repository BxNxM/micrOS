from LM_neopixel import __init_NEOPIXEL, segment
#from time import sleep_ms

INDEX_OFFSET = 0


def __draw(gen_obj, ms=20, shift=False):
    """
    :param gen_obj: Colors generator object
    :ms: speed / wait in ms
    :return: None
    """
    if shift:
        gen_obj = __offset(gen_obj)
    for i, c in enumerate(gen_obj):
        r, g, b = c
        segment(int(r), int(g), int(b), s=i)
        #sleep_ms(ms)


def __offset(gen_obj):
    global INDEX_OFFSET
    pixel_cnt = __init_NEOPIXEL().n
    pos = INDEX_OFFSET
    buffer = [(0, 0, 0) for _ in range(0, pixel_cnt)]
    for k in range(pos, pixel_cnt):
        buffer[k] = gen_obj.__next__()
    for k in range(0, pos):
        buffer[k] = gen_obj.__next__()
    INDEX_OFFSET = pos+1 if INDEX_OFFSET < pixel_cnt else 0
    return tuple(buffer)


def meteor(r, g, b, shift=False):
    def effect(r, g, b, pixel_cnt, fade_step):
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
    pixel_cnt = __init_NEOPIXEL().n
    fade_step = float(1.0 / pixel_cnt)
    # Construct generator object
    g = effect(r, g, b, pixel_cnt, fade_step)
    # Draw generator obj
    __draw(g, shift=shift)
    return 'Meteor R{}:G{}:B{} N:{}'.format(r, g, b, pixel_cnt)


def lmdep():
    return 'LM_neopixel'


def help():
    return 'meteor r=<0-255> g=<0-255> b=<0-255>'
