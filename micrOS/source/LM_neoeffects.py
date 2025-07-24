from LM_neopixel import load as neoload, segment, Data, status, pinmap as pm
from random import randint
from Types import resolve
from Common import manage_task, AnimationPlayer


#################################
#  NEOPIXEL EFFECT DRAWER CLASS #
#################################

class DrawEffectV2(AnimationPlayer):
    INSTANCE = None

    def __init__(self, pix_cnt=24):
        super().__init__(tag="neoeffects")
        neoload(ledcnt=pix_cnt)
        DrawEffectV2.INSTANCE = self

    @staticmethod
    def normalize_index(value) -> int:
        return value % Data.NEOPIXEL_OBJ.n

    @staticmethod
    def color_code(r:int=None, g:int=None, b:int=None) -> tuple[float, float, float]:
        _r, _g, _b, _ = Data.DCACHE
        r = _r if r is None else r
        g = _g if g is None else g
        b = _b if b is None else b
        return r, g, b

    def update(self, index:int, r:int|float, g:int|float, b:int|float):
        # Animation player will call this method to update pixels.
        segment(r=int(r), g=int(g), b=int(b), s=index, cache=False, write=False)

    def draw(self):
        # Animation player will call this method to update pixels.
        Data.NEOPIXEL_OBJ.write()

    def clear(self):
        # Animation player will call this method to update pixels.
        for i in range(0, Data.NEOPIXEL_OBJ.n):
            self.update(i, 0, 0, 0)
        self.draw()

##################################################################################
#                                  EFFECTS                                       #
##################################################################################

def meteor(speed_ms:int=60, shift:bool=True, batch:bool=True):
    """
    Meteor effect
    :param speed_ms: animation speed in milliseconds
    :param shift: automatic effect rotation
    :param batch: batch mode
    :return str: verdict
    """
    def effect_meteor():
        """
        Describe one full length color map
        :return: yield tuple with r,g,b
        """
        nonlocal shift, pix_cnt
        max_offset = pix_cnt if shift else 1
        for offset in range(0, max_offset):
            r, g, b = DrawEffectV2.color_code()
            for pixel in range(0, pix_cnt):
                br, norm = 0.6, pixel/pix_cnt
                fade = br * norm ** 0.9         # exponent < 1 simulates log-like curve
                yield DrawEffectV2.normalize_index(pixel+offset), r*fade, g*fade, b*fade

    neoeffect = load()
    pix_cnt = Data.NEOPIXEL_OBJ.n
    return neoeffect.play(effect_meteor, speed_ms=speed_ms, bt_draw=batch, bt_size=pix_cnt)


def cycle(speed_ms:int=60, shift:bool=True, batch:bool=True):
    """
    Cycle effect
    :param speed_ms: animation speed in milliseconds
    :param shift: automatic effect rotation
    :param batch: enable/disable batch update mode
    """
    def effect_cycle():
        """
        Describe one full length color map
        :return: yield tuple with index, r,g,b
        """
        nonlocal shift
        max_offset = Data.NEOPIXEL_OBJ.n if shift else 1
        for offset in range(0, max_offset):
            r, g, b = DrawEffectV2.color_code()
            lr, lg, lb = int(r * 0.1), int(g * 0.1), int(b * 0.1)
            # Clean last pixel
            yield DrawEffectV2.normalize_index(offset-1), 0, 0, 0
            # Draw pattern
            yield DrawEffectV2.normalize_index(offset), lr, lg, lb
            yield DrawEffectV2.normalize_index(offset + 1), r, g, b
            yield DrawEffectV2.normalize_index(offset + 2), lr, lg, lb

    return load().play(effect_cycle, speed_ms=speed_ms, bt_draw=batch, bt_size=4)


def rainbow(speed_ms=20, br=15, batch=True):
    def _wheel(pos):
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

    def effect_rainbow():
        """
        :param cnt: led segment count
        :param br: max brightness 0-100%
        :param step: step size
        """
        nonlocal pix_cnt, br
        color_step = 3
        for color_wheel in range(0, 255, color_step):
            for index in range(0, pix_cnt):
                rc_index = (index * 256 // pix_cnt) + color_wheel
                r, g, b = _wheel(rc_index & 255)
                yield DrawEffectV2.normalize_index(index+color_wheel), round(r*br*0.01), round(g*br*0.01), round(b*br*0.01)

    neoeffect = load()
    pix_cnt = Data.NEOPIXEL_OBJ.n
    return neoeffect.play(effect_rainbow, speed_ms=speed_ms, bt_draw=batch, bt_size=pix_cnt)


def fire(speed_ms:int=150, br:int=30, batch:bool=True):
    """
    Fire effect
    :param speed_ms: animation speed in milliseconds
    :param br: max brightness 0-100%
    :param batch: batch update
    """
    def effect_fire():
        nonlocal pix_cnt, br
        max_value = int(255 * (br/100))
        for index in range(pix_cnt):
            r, g, b = DrawEffectV2.color_code()
            rand_percent = float(round(randint(1, max_value)/max_value, 2))
            new_r = min(max(int(r * rand_percent), 0), max_value)
            new_g = min(max(int(g * rand_percent), 0), max_value)
            new_b = min(max(int(b * rand_percent), 0), max_value)
            yield index, new_r, new_g, new_b

    neoeffect = load()
    pix_cnt = Data.NEOPIXEL_OBJ.n
    return neoeffect.play(effect_fire, speed_ms=speed_ms, bt_draw=batch, bt_size=pix_cnt)


def shader(offset=0, size=6):
    def effect_shader():
        nonlocal size, offset, neoeffect
        pix_cnt = Data.NEOPIXEL_OBJ.n
        # Conditional value load - with neopixel cache
        r, g, b = DrawEffectV2.color_code()
        # calculate 0->24 range
        _slice1 = pix_cnt if size + offset > pix_cnt else size + offset
        # calculate 24->0-> range (overflow)
        _slice2 = size + offset - pix_cnt if size + offset > pix_cnt else 0
        for i in range(0, pix_cnt):
            if offset <= i < _slice1 or 0 <= i < _slice2:
                neoeffect.update(i, 0, 0, 0)
            else:
                neoeffect.update(i, r, g, b)
        neoeffect.draw()

    neoeffect = load()
    effect_shader()
    return "Shader was set."


def color(r:int=None, g:int=None, b:int=None):
    """
    Set color buffer - for runtime effect color change
    :param r: red channel 0-255 (default: None - cached value)
    :param g: green channel 0-255 (default: None - cached value)
    :param b: blue channel 0-255 (default: None - cached value)
    :return dict: rgb status - states: R, G, B, S
    """
    # Conditional value load - with neopixel cache
    r, g, b = DrawEffectV2.color_code(r, g, b)
    Data.DCACHE[0] = r
    Data.DCACHE[1] = g
    Data.DCACHE[2] = b
    return status()


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


def stop():
    """
    Stop all running (neo)effects tasks
    """
    player_info = load().stop()
    random_task = manage_task("neoeffects.random", "kill")
    return f"{player_info}\n{random_task}"

def control(speed_ms=None, batch:bool=None):
    """
    Change the speed of frame generation for animations.
    """
    data = load().control(play_speed_ms=speed_ms, bt_draw=batch)
    _speed_ms = data.get("player_speed", None)
    return f"Control state: {data} (speed: {_speed_ms}ms)"


def load(pixel_cnt=24):
    """
    Load LM_neopixel and DrawEffectV2
    """
    if DrawEffectV2.INSTANCE is None:
        DrawEffectV2(pix_cnt=pixel_cnt)
    return DrawEffectV2.INSTANCE

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
    return resolve(('load pixel_cnt=24',
                             'meteor speed_ms=60 shift=True batch=True',
                             'BUTTON meteor speed_ms=60',
                             'cycle speed_ms=60 shift=True batch=True',
                             'BUTTON cycle speed_ms=60',
                             'rainbow speed_ms=20 br=15 batch=True',
                             'BUTTON rainbow',
                             'fire speed_ms=150 br=30 batch=True',
                             'BUTTON fire speed_ms=150',
                             'BUTTON stop',
                             'shader offset=0 size=6',
                             'control speed_ms=None batch=None',
                             'random max_val=255',
                             'pinmap',
                             'COLOR color r=<0-255-10> g b'
                    ), widgets=widgets)
