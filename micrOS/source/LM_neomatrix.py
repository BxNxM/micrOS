from neopixel import NeoPixel
from machine import Pin
from utime import sleep_ms

from microIO import bind_pin
from Types import resolve
from Common import manage_task, AnimationPlayer


class NeoPixelMatrix(AnimationPlayer):
    INSTANCE = None
    DEFAULT_COLOR = (100, 23, 0)  # Default color for the matrix

    def __init__(self, width: int = 8, height: int = 8, pin: int = 0):
        super().__init__(tag="neomatrix")
        self.width = width
        self.height = height
        self.num_pixels = width * height
        self.pixels = NeoPixel(Pin(pin, Pin.OUT), self.num_pixels)
        self._color_buffer = [(0, 0, 0)] * self.num_pixels      # Store original RGB values
        self._brightness = 0.25                                 # Brightness level, default 25%
        NeoPixelMatrix.INSTANCE = self

    def update(self, x:int, y:int, color:tuple[int, int, int]):
        # Animation player will call this method to update pixels.
        self.set_pixel(x, y, color)

    def draw(self):
        # Animation player will call this method to update the display.
        self.pixels.write()

    def clear(self):
        # Animation player will call this method to clear the display.
        for i in range(self.num_pixels):
            # Write pixel buffer before write to ws2812
            self.pixels[i] = (0, 0, 0)
        # Send buffer to device
        self.draw()

    def _coord_to_index(self, x: int, y: int, zigzag:bool=True):
        """
        Zigzag layout: even rows left-to-right, odd rows right-to-left
        """
        if (zigzag is None or zigzag) and y % 2 == 0:
            return y * self.width + x
        return y * self.width + (self.width - 1 - x)

    def _index_to_coord(self, index: int, zigzag:bool=True) -> tuple[int, int]:
        """
        Converts a linear index to (x, y) coordinates.
        Zigzag layout: even rows left-to-right, odd rows right-to-left.
        """
        y = index // self.width
        x = index % self.width
        if (zigzag is None or zigzag) and y % 2 == 1:
            x = self.width - 1 - x
        return x, y

    def _rgb_to_grb_with_br(self, color: tuple[int, int, int]):
        """
        Converts RGB to GRB with brightness adjustment.
        """
        def scale(val):
            return max(0, min(255, int(val * self._brightness)))

        return scale(color[1]), scale(color[0]), scale(color[2])

    def set_pixel(self, x: int, y: int, color: tuple[int, int, int], zigzag:bool=True):
        """
        Set pixel at (x, y) with RGB
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self._coord_to_index(x, y, zigzag=zigzag)
            self._color_buffer[index] = color  # store original RGB for brightness control
            self.pixels[index] = self._rgb_to_grb_with_br(color)

    def color(self, color: tuple[int, int, int]):
        """
        Fill color OR Animation color change.
        :param color: tuple[int, int, int] range: 0-255
        :return: str
        """
        r, g, b = max(0, min(color[0], 255)), max(0, min(color[1], 255)), max(0, min(color[2], 255))
        color = (r, g, b)
        NeoPixelMatrix.DEFAULT_COLOR = color
        if manage_task(self._task_tag, "isbusy"):
            return f"Set animation color to {color}"
        for i in range(self.num_pixels):
            self._color_buffer[i] = color
            # Write pixel buffer before write to ws2812
            self.pixels[i] = self._rgb_to_grb_with_br(color)
        # Send buffer to device
        self.draw()
        return f"Set all pixels to {color}"

    def brightness(self, br: int):
        """
        Change the brightness of all pixels.
        """
        br = max(0, min(br, 100))  # clamp brightness to 0–100%
        self._brightness = br / 100.0
        # Set color matrix brightness
        for i, color in enumerate(self._color_buffer):
            # Write pixel buffer before write to ws2812
            self.pixels[i] = self._rgb_to_grb_with_br(color)
        self.draw()
        return f"Set brightness to {br}%"

    def draw_colormap(self, bitmap:list):
        """
        Draw a bitmap on the Neopixel
        bitmap: [(x, y, (r, g, b)),
                 (x, y, (r, g, b)), ...]
        """
        if len(bitmap) == 0:
            self.clear()
            return
        for bm in bitmap:
            x, y, color = bm
            self.set_pixel(x, y, color, zigzag=False)
        self.draw()

    def export_colormap(self):
        """
        Export the current screen as bitmap
        """
        colormap = []
        for i, color in enumerate(self._color_buffer):
            x, y = self._index_to_coord(i, zigzag=False)
            colormap.append((x, y, color))
        return colormap

##########################################################################################################
##########################################################################################################
# --- Example usage with micrOS framework ---

def load(width=8, height=8):
    """
    Load NeoPixelMatrix instance. If not already loaded
    """
    if NeoPixelMatrix.INSTANCE is None:
        NeoPixelMatrix(width=width, height=height, pin=bind_pin('neop'))
    return NeoPixelMatrix.INSTANCE


def pixel(x, y, color=None, show=True):
    """
    Set pixel at (x,y) to RGB color.
    """
    color = NeoPixelMatrix.DEFAULT_COLOR if color is None else color
    matrix = load()
    matrix.set_pixel(x, y, color)
    if show:
        matrix.draw()
        return "Set and draw color"
    return "Set color"


def draw():
    """
    Draw the current frame manually on the screen.
    """
    load().draw()
    return "Draw screen"


def clear():
    """
    Clear the screen.
    """
    load().clear()
    return "Clear screen"


def color_fill(r: int, g: int, b: int):
    """
    Fill the screen with a solid color.
    OR
    Change animation color (when possible)
    """
    return load().color((r, g, b))


def brightness(br: int):
    """
    Change the brightness of the display. (0-100)
    """
    return load().brightness(br)


def control(speed_ms=None, bt_draw:bool=None):
    """
    Change the speed of frame generation for animations.
    """
    data = load().control(play_speed_ms=speed_ms, bt_draw=bt_draw)
    _speed_ms = data.get("player_speed", None)
    return f"Control state: {data} (speed: {_speed_ms}ms)"


def stop():
    """
    Stop the current animation
    """
    return load().stop()


def draw_colormap(bitmap):
    try:
        load().draw_colormap(bitmap)
    except Exception as e:
        return str(e)
    return "Done."


def get_colormap():
    return load().export_colormap()

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def rainbow(speed_ms=0):
    def effect_rainbow():
        def hsv_to_rgb(h, s, v):
            max_color = 150   #255
            h = float(h)
            s = float(s)
            v = float(v)
            i = int(h * 6.0)
            f = (h * 6.0) - i
            p = v * (1.0 - s)
            q = v * (1.0 - s * f)
            t = v * (1.0 - s * (1.0 - f))
            i = i % 6
            if i == 0:
                r, g, b = v, t, p
            elif i == 1:
                r, g, b = q, v, p
            elif i == 2:
                r, g, b = p, v, t
            elif i == 3:
                r, g, b = p, q, v
            elif i == 4:
                r, g, b = t, p, v
            elif i == 5:
                r, g, b = v, p, q
            return int(r * max_color), int(g * max_color), int(b * max_color)

        width = 8
        height = 8
        total_frames = 64

        for frame in range(total_frames):
            for y in range(height):
                for x in range(width):
                    index = y * width + x
                    hue = ((index + frame) % 64) / 64.0
                    r, g, b = hsv_to_rgb(hue, 1.0, 0.7)
                    yield x, y, (r, g, b)

    return load().play(effect_rainbow, speed_ms=speed_ms, bt_draw=True, bt_size=8)


def snake(speed_ms:int=30, length:int=5):
    def effect_snake():
        clear_color = (0, 0, 0)
        total_pixels = 8 * 8
        total_steps = total_pixels + length  # run just past the end to clear tail

        for step in range(total_steps):
            # 1) clear the tail pixel once the snake is longer than `length`
            if step >= length:
                tail_idx = step - length
                tx, ty = tail_idx % 8, tail_idx // 8
                yield tx, ty, clear_color

            # 2) draw the snake segments with decreasing brightness
            for i in range(length):
                seg_idx = step - i
                if 0 <= seg_idx < total_pixels:
                    x, y = seg_idx % 8, seg_idx // 8
                    br = 1.0 - (i / length) ** 0.6
                    r, g, b = NeoPixelMatrix.DEFAULT_COLOR
                    color = (int(r * br), int(g * br), int(b * br))
                    yield x, y, color

    return load().play(effect_snake, speed_ms=speed_ms, bt_draw=False)


def cube(speed_ms=10):
    def effect_cube(max_radius:int = 3):
        """
        Generator yielding (x, y, color) for a centered 2×2 square ("cube")
        that expands outward to `max_radius` then collapses back.
        """
        width, height = 8, 8
        # Center the 2×2 core in an 8×8 grid
        cx, cy = width // 2 - 1, height // 2 - 1

        # Expansion phase: radius 0 (2×2) up to max_radius
        for r in range(0, max_radius + 1):
            for dx in range(-r, r + 2):
                for dy in range(-r, r + 2):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < width and 0 <= y < height:
                        yield x, y, NeoPixelMatrix.DEFAULT_COLOR
        # Clear matrix
        try:
            NeoPixelMatrix.INSTANCE.clear()
        except:
            pass
        # Collapse phase: back down, skipping the largest to avoid duplicate
        for r in range(max_radius - 1, -1, -1):
            for dx in range(-r, r + 2):
                for dy in range(-r, r + 2):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < width and 0 <= y < height:
                        yield x, y, NeoPixelMatrix.DEFAULT_COLOR

    return load().play(effect_cube, speed_ms=speed_ms, bt_draw=False)


def help(widgets=False):
    return resolve(('load width=8 height=8',
                             'pixel x y color=(10, 3, 0) show=True',
                             'BUTTON clear',
                             'COLOR color_fill r=<0-255-5> g=<0-255-5> b=<0-255-5>',
                             'SLIDER brightness br=<0-60-2>',
                             'BUTTON stop',
                             'BUTTON snake speed_ms=50 length=5',
                             'BUTTON rainbow',
                             'BUTTON cube speed_ms=10',
                             'SLIDER control speed_ms=<1-200-2> bt_draw=None',
                             'draw_colormap bitmap=[(0,0,(10,2,0)),(x,y,color),...]',
                             'get_colormap'
                    ), widgets=widgets)
