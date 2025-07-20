from neopixel import NeoPixel
from machine import Pin
from utime import sleep_ms

from microIO import bind_pin
from Types import resolve
from Common import micro_task, manage_task


class AnimationPlayer:
    """
    Generic async animation (generator) player.
    """

    def __init__(self, animation:callable=None, realtime_draw:bool=True, tag:str=None):
        """
        Initialize the AnimationPlayer with an optional animation.
        :param animation: Function to GENERATE animation data
        :param realtime_draw: If True - draw each change immediately, otherwise draw complete frames.
        :param tag: Optional task tag for micro_task management.
        """
        self.animation:callable = None
        self.realtime_draw:bool = realtime_draw
        self.player_speed_ms:int = 10
        self._main_tag:str = tag if tag else "animation"
        self._set_animation(animation)
        self._running:bool = True

    def _set_animation(self, animation) -> bool:
        """
        Set/Change the current animation to be played.
        """
        if animation is None:
            return False
        if callable(animation):
            self.animation = animation
            return True
        return False

    async def _player(self):
        """
        Async task to play the current animation.
        """

        with micro_task(tag=f"{self._main_tag}.player") as my_task:
            current_animation = self.animation

            while self._running:
                my_task.out = f"Play {self.animation.__name__} ({self.player_speed_ms}ms/frame)"
                try:
                    # Clear the display before each frame
                    if self.realtime_draw:
                        self.clear()
                    for data in self.animation():
                        # Check if animation has changed (+ stop trigger)
                        if self._running and self.animation != current_animation:
                            current_animation = self.animation
                            # Animation changed — restarting loop.
                            break
                        # Update data cache
                        self.update(*data)
                        if self.realtime_draw:
                            # Draw each change
                            self.draw()
                            await my_task.feed(sleep_ms=self.player_speed_ms)
                    if not self.realtime_draw:
                        # Draw complete frame only after loop completes
                        self.draw()
                        await my_task.feed(sleep_ms=self.player_speed_ms)
                except IndexError:
                    # Restart animation if IndexError occurs
                    pass
                except Exception as e:
                    print(f"Error: {e}")
                    break

    def play(self, animation=None, speed_ms=None, rt_draw=True):
        """
        Play animation via generator function.
        :param animation: Animation generator function.
        :param speed_ms: Speed of the animation in milliseconds. (min.: 3ms)
        :param rt_draw: Real-time drawing flag.
        """

        if animation is not None:
            if not self._set_animation(animation):
                return "Invalid animation"

        if self.animation is None:
            return "No animation to play"

        if isinstance(speed_ms, int):
            self.player_speed_ms = speed_ms if speed_ms > 1 else 2

        if isinstance(rt_draw, bool):
            self.realtime_draw = rt_draw

        # Ensure async loop set up correctly. (After stop operation, it is needed)
        self._running = True

        # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
        state = micro_task(tag=f"{self._main_tag}.player", task=self._player())
        return "Starting" if state else "Already running..."


    def stop(self):
        """
        Stop the animation.
        """
        self._running = False
        return "Stop animation player"


    def update(self, *arg, **kwargs):
        """
        Child class must implement this method to handle drawing logic.
        """
        raise NotImplementedError("Child class must implement update method.")

    def draw(self):
        """
        Draw the current frame.
        """
        raise NotImplementedError("Child class must implement draw method.")

    def clear(self):
        """
        Clear the display.
        """
        raise NotImplementedError("Child class must implement clear method.")

##########################################################################################################
##########################################################################################################

class NeoPixelMatrix(AnimationPlayer):
    INSTANCE = None
    DEFAULT_COLOR = (20, 5, 0)  # Default color for the matrix

    def __init__(self, width: int = 8, height: int = 8, pin: int = 0):
        super().__init__(tag="neomatrix")
        self.width = width
        self.height = height
        self.num_pixels = width * height
        self.pixels = NeoPixel(Pin(pin, Pin.OUT), self.num_pixels)
        self.buffer = [(0, 0, 0)] * self.num_pixels  # Store original RGB values
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
            self.buffer[i] = (0, 0, 0)
            self.pixels[i] = (0, 0, 0)
        self.draw()

    def _coord_to_index(self, x: int, y: int):
        # Zigzag layout: even rows left-to-right, odd rows right-to-left
        if y % 2 == 0:
            return y * self.width + x
        return y * self.width + (self.width - 1 - x)

    @staticmethod
    def _rgb_to_grb(color: tuple[int, int, int]):
        return color[1], color[0], color[2]  # GRB format

    def set_pixel(self, x: int, y: int, color: tuple[int, int, int]):
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self._coord_to_index(x, y)
            self.buffer[index] = color  # store original RGB for brightness control
            self.pixels[index] = self._rgb_to_grb(color)

    def color(self, color: tuple[int, int, int]):
        if manage_task(f"{self._main_tag}.player", "isbusy"):
            NeoPixelMatrix.DEFAULT_COLOR = color
            return f"Set animation color to {color}"
        for i in range(self.num_pixels):
            self.buffer[i] = color
            NeoPixelMatrix.DEFAULT_COLOR = color
            self.pixels[i] = self._rgb_to_grb(color)
        self.draw()
        return f"Set all pixels to {color}"

    def brightness(self, br: int):
        br = max(0, min(br, 100))  # clamp brightness to 0–100%
        # Set color matrix brightness
        for i, (r, g, b) in enumerate(self.buffer):
            scaled = (
                min(255, max(0, int(r * br / 100))),
                min(255, max(0, int(g * br / 100))),
                min(255, max(0, int(b * br / 100)))
            )
            self.pixels[i] = self._rgb_to_grb(scaled)
        self.draw()


##########################################################################################################
##########################################################################################################
# --- Example usage with micrOS framework ---

def load(width=8, height=8):
    if NeoPixelMatrix.INSTANCE is None:
        NeoPixelMatrix(width=width, height=height, pin=bind_pin('neop'))
    return NeoPixelMatrix.INSTANCE


def pixel(x, y, color=None, show=True):
    color = NeoPixelMatrix.DEFAULT_COLOR if color is None else color
    matrix = load()
    matrix.set_pixel(x, y, color)
    if show:
        matrix.draw()
        return "Set and draw color"
    return "Set color"


def draw():
    load().draw()
    return "Draw screen"


def clear():
    load().clear()
    return "Clear screen"


def color_fill(r: int, g: int, b: int):
    return load().color((r, g, b))


def brightness(br: int):
    load().brightness(br)
    return f"Set brightness to {br}%"


def stop():
    return load().stop()


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def rainbow(speed_ms=2, rt_draw=False):
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
                NeoPixelMatrix.INSTANCE.draw()

    return load().play(effect_rainbow, speed_ms=speed_ms, rt_draw=rt_draw)


def snake(speed_ms:int=50, length:int=5):
    def effect_snake():
        clear_color = (0, 0, 0)
        total_steps = 8 * 8 + length  # run just past the end to clear tail

        for step in range(total_steps):
            # 1) clear the tail pixel once the snake is longer than `length`
            if step >= length:
                tail_idx = step - length
                tx, ty = tail_idx % 8, tail_idx // 8
                yield tx, ty, clear_color

            # 2) move the head (only while head index < 64)
            if step < 8 * 8:
                hx, hy = step % 8, step // 8
                yield hx, hy, NeoPixelMatrix.DEFAULT_COLOR

    return load().play(effect_snake, speed_ms=speed_ms)


def cube(speed_ms=10):
    def effect_cube(max_radius:int = 3):
        """
        Generator yielding (x, y, color) for a centered 2×2 square ("cube")
        that expands outward to `max_radius` then collapses back.
        Each full frame is produced by yielding all its pixels; the AnimationPlayer
        will clear between frames and draw per its realtime_draw setting.
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

        # Collapse phase: back down, skipping the largest to avoid duplicate
        for r in range(max_radius - 1, -1, -1):
            for dx in range(-r, r + 2):
                for dy in range(-r, r + 2):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < width and 0 <= y < height:
                        yield x, y, NeoPixelMatrix.DEFAULT_COLOR

    return load().play(effect_cube, speed_ms=speed_ms)


def help(widgets=False):
    return resolve(('load width=8 height=8',
                             'pixel x y color=(10, 3, 0) show=True',
                             'BUTTON clear',
                             'COLOR color_fill r=<0-255> g=<0-255> b=<0-255>',
                             'SLIDER brightness br=<0-100>',
                             'BUTTON stop',
                             'BUTTON snake speed_ms=50 length=5',
                             'BUTTON rainbow speed_ms=2',
                             'BUTTON cube'), widgets=widgets)
