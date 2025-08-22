from neopixel import NeoPixel
from machine import Pin
from utime import sleep_ms

from microIO import bind_pin
from Types import resolve
from Common import manage_task, AnimationPlayer, web_dir, syslog, web_endpoint


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
        self._brightness = 0.20                                 # Brightness level, default 20%
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
            self._color_buffer[i] = (0, 0, 0)
        # Send buffer to device
        self.draw()

    def _coord_to_index(self, x: int, y: int, zigzag:bool=True):
        """
        Zigzag layout: even rows left-to-right, odd rows right-to-left
        """
        if zigzag is None or zigzag:
            if y % 2 == 0:
                return y * self.width + x
            return y * self.width + (self.width - 1 - x)
        return y * self.width + x

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
        web_endpoint('matrixDraw', _web_endpoint_clb, auto_enable=False)
    return NeoPixelMatrix.INSTANCE


def _web_endpoint_clb():
    try:
        with open(web_dir('matrix_draw.html'), 'r') as html:
            html_content = html.read()
        return 'text/html', html_content
    except Exception as e:
        syslog(f"[ERR] neomatrix web: {e}")
        html_content = None
    return 'text/plain', f'html_content error: {html_content}'


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
    def _effect_rainbow():
        def _hsv_to_rgb(h, s, v):
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
                    r, g, b = _hsv_to_rgb(hue, 1.0, 0.7)
                    yield x, y, (r, g, b)

    return load().play(_effect_rainbow, speed_ms=speed_ms, bt_draw=True, bt_size=8)


def snake(speed_ms:int=30, length:int=5):
    def _effect_snake():
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

    return load().play(_effect_snake, speed_ms=speed_ms, bt_draw=False)


def spiral(speed_ms=40):
    def _effect_spiral(trail=12, hold=6):
        """
        Center-out spiral with row-prewarp so the visual is continuous
        even when set_pixel() applies zigzag=True internally.
        """
        try:
            W = NeoPixelMatrix.INSTANCE.width
            H = NeoPixelMatrix.INSTANCE.height
        except:
            W = H = 8

        # --- build center-out spiral path in true matrix coords (x,y) ---
        # exact center on odd sizes; upper-left of center 2x2 on even sizes
        cx = (W // 2 - 1) if (W % 2 == 0) else (W // 2)
        cy = (H // 2 - 1) if (H % 2 == 0) else (H // 2)

        x, y = cx, cy
        path, seen = [], set()

        def _add(ax, ay):
            if 0 <= ax < W and 0 <= ay < H and (ax, ay) not in seen:
                seen.add((ax, ay))
                path.append((ax, ay))

        _add(x, y)
        dirs = ((1, 0), (0, 1), (-1, 0), (0, -1))  # R, D, L, U
        step_len, d = 1, 0
        while len(path) < W * H:
            for _ in range(2):
                dx, dy = dirs[d & 3]
                for _ in range(step_len):
                    x += dx; y += dy
                    _add(x, y)
                    if len(path) >= W * H: break
                d += 1
                if len(path) >= W * H: break
            step_len += 1

        # --- PREWARP ---
        # Cancel the internal zigzag mapping: flip x on odd rows so
        # set_pixel(zigzag=True) flips it back -> visually linear.
        def _warp(ax, ay):
            return (W - 1 - ax, ay) if (ay & 1) else (ax, ay)

        r0, g0, b0 = NeoPixelMatrix.DEFAULT_COLOR
        off = (0, 0, 0)

        def _shade(k):
            k = max(0.0, min(1.0, k)) ** 0.9
            return (int(r0 * k), int(g0 * k), int(b0 * k))

        try:
            NeoPixelMatrix.INSTANCE.clear()
        except:
            pass

        # expand with tail
        for n in range(len(path)):
            clear_at = n - trail - 1
            if clear_at >= 0:
                cx_, cy_ = _warp(*path[clear_at])
                yield cx_, cy_, off

            start = 0 if n < trail else (n - trail + 1)
            span = max(1, n - start + 1)
            for i in range(start, n + 1):
                k = (i - start + 1) / span
                px, py = _warp(*path[i])
                yield px, py, _shade(k)

        # brief hold
        hx, hy = _warp(*path[-1])
        for _ in range(hold):
            yield hx, hy, _shade(1.0)

        # shrink with fading tail
        for n in range(len(path) - 1, -1, -1):
            px, py = _warp(*path[n])
            yield px, py, off
            start = max(0, n - trail + 1)
            span = max(1, n - start)
            for i in range(start, n):
                k = (i - start + 1) / span
                qx, qy = _warp(*path[i])
                yield qx, qy, _shade(k)

    return load().play(_effect_spiral, speed_ms=speed_ms, bt_draw=True, bt_size=8)


def help(widgets=False):
    return resolve(('load width=8 height=8',
                             'pixel x y color=(10, 3, 0) show=True',
                             'BUTTON clear',
                             'COLOR color_fill r=<0-255-5> g=<0-255-5> b=<0-255-5>',
                             'SLIDER brightness br=<0-60-2>',
                             'BUTTON stop',
                             'BUTTON snake speed_ms=50 length=5',
                             'BUTTON rainbow',
                             'BUTTON spiral speed_ms=40',
                             'SLIDER control speed_ms=<1-200-2> bt_draw=None',
                             'draw_colormap bitmap=[(0,0,(10,2,0)),(x,y,color),...]',
                             'get_colormap'
                    ), widgets=widgets)
