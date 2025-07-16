from neopixel import NeoPixel
from machine import Pin
from utime import sleep_ms


class NeoPixelMatrix:
    INSTANCE = None

    def __init__(self, width: int = 8, height: int = 8, pin: int = 0):
        self.width = width
        self.height = height
        self.num_pixels = width * height
        self.pixels = NeoPixel(Pin(pin, Pin.OUT), self.num_pixels)
        self.buffer = [(0, 0, 0)] * self.num_pixels  # Store original RGB values
        NeoPixelMatrix.INSTANCE = self

    def _coord_to_index(self, x: int, y: int):
        # Zigzag layout: even rows left-to-right, odd rows right-to-left
        if y % 2 == 0:
            return y * self.width + x
        else:
            return y * self.width + (self.width - 1 - x)

    @staticmethod
    def _rgb_to_grb(color: tuple[int, int, int]):
        return color[1], color[0], color[2]  # GRB format

    def set_pixel(self, x: int, y: int, color: tuple[int, int, int]):
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self._coord_to_index(x, y)
            self.buffer[index] = color  # store original RGB for brightness control
            self.pixels[index] = self._rgb_to_grb(color)

    def clear(self):
        for i in range(self.num_pixels):
            self.buffer[i] = (0, 0, 0)
            self.pixels[i] = (0, 0, 0)
        self.show()

    def fill(self, color: tuple[int, int, int]):
        for i in range(self.num_pixels):
            self.buffer[i] = color
            self.pixels[i] = self._rgb_to_grb(color)
        self.show()

    def brightness(self, br: int):
        br = max(0, min(br, 100))
        for i, (r, g, b) in enumerate(self.buffer):
            scaled = (
                r * br // 100,
                g * br // 100,
                b * br // 100
            )
            self.pixels[i] = self._rgb_to_grb(scaled)
        self.show()

    def show(self):
        self.pixels.write()


# --- Example usage with micrOS framework ---
from microIO import bind_pin

def load(width=8, height=8):
    if NeoPixelMatrix.INSTANCE is None:
        NeoPixelMatrix(width=width, height=height, pin=bind_pin('neop'))
    return NeoPixelMatrix.INSTANCE


def pixel(x, y, color=(10, 3, 0), show=True):
    matrix = load()
    matrix.set_pixel(x, y, color)
    if show:
        matrix.show()


def draw():
    load().show()


def clear():
    load().clear()


def fill(r: int, g: int, b: int):
    load().fill((r, g, b))


def brightness(br: int):
    load().brightness(br)


# ------------------------------------------

def _effect_snake(speed_ms=1):
    clear()
    for i in range(64):
        x, y = i % 8, i // 8
        pixel(x, y)
        sleep_ms(speed_ms)


def _effect_rainbow(speed_ms=1, cycles=5):
    clear()

    def hsv_to_rgb(h, s, v):
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
        return int(r * 255), int(g * 255), int(b * 255)

    width = 8
    height = 8
    total_frames = 64 * cycles

    for frame in range(total_frames):
        for y in range(height):
            for x in range(width):
                index = y * width + x
                hue = ((index + frame) % 64) / 64.0
                r, g, b = hsv_to_rgb(hue, 1.0, 0.2)
                pixel(x, y, color=(r, g, b), show=False)
            draw()
        sleep_ms(speed_ms)


def test(speed_ms=50):
    _effect_snake(speed_ms)
    _effect_rainbow(speed_ms)


def help(widgets=False):
    return ('load width=8 height=8',
            'pixel x y color=(10, 3, 0) show=True',
            'clear',
            'fill r=<0-255> g=<0-255> b=<0-255>',
            'brightness br=<0-100>',
            'test')
