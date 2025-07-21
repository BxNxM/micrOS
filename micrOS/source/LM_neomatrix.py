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

    def __init__(self, animation:callable=None, realtime_draw:bool=True,
                 batch_draw:bool=False, batch_size:int|None=None, tag:str=None):
        """
        Initialize the AnimationPlayer with an optional animation.
        :param animation: Function to GENERATE animation data
        :param realtime_draw: If True - draw each change immediately, otherwise draw complete frames.
        :param tag: Optional task tag for micro_task management.
        :param batch_draw: If True - draw in batches
        :param batch_size: Number of pixels per batch when drawing
        """
        self.animation:callable = None
        self.realtime_draw:bool = realtime_draw
        self.batch_draw:bool = batch_draw
        self._batch_size:int = batch_size if isinstance(batch_size, int) else 8
        self._player_speed_ms:int = 10
        self._main_tag:str = tag if tag else "animation"
        if animation is not None and not self._set_animation(animation):
            raise Exception("Invalid animation function provided.")
        self._running:bool = True

    def _set_animation(self, animation:callable) -> bool:
        """
        Set/Change the current animation to be played.
        """
        if callable(animation):
            self.animation = animation
            return True
        return False

    async def _render(self, my_task):
        current_animation = self.animation
        frame_counter = 0
        # Clear the display before each frame
        if self.realtime_draw:
            self.clear()
        for data in self.animation():
            # Check if animation has changed under the loop
            if not self._running or self.animation != current_animation:
                # Animation changed — restarting loop.
                break
            # Update data cache
            self.update(*data)
            # Real-time draw mode
            if self.realtime_draw:
                # Draw each change
                self.draw()
                await my_task.feed(sleep_ms=self._player_speed_ms)
            # Batched draw mode
            if self.batch_draw:
                frame_counter += 1
                if frame_counter >= self._batch_size:
                    self.draw()
                    frame_counter = 0
                # Test async speed (0.001 ms)
                await my_task.feed(sleep_ms=self._player_speed_ms)
        if self.batch_draw:
            # Draw after generator exhausted in batch mode.
            self.draw()
            await my_task.feed(sleep_ms=self._player_speed_ms)

    async def _player(self):
        """
        Async task to play the current animation.
        """

        with micro_task(tag=f"{self._main_tag}.player") as my_task:
            while self._running:
                my_task.out = f"Play {self.animation.__name__} ({self._player_speed_ms}ms/frame)"
                try:
                    await self._render(my_task)
                except IndexError:
                    # Restart animation if IndexError occurs
                    my_task.out = "Restart animation"
                    pass
                except Exception as e:
                    my_task.out = f"Error: {e}"
                    break
            my_task.out = f"Animation stopped...{my_task.out}"

    def control(self, play_speed_ms:int|None, rt_draw:bool=None,
                      bt_draw:bool=None, bt_size:int=None):
        """
        Set/Get current play speed of the animation.
        :param play_speed_ms: player loop speed in milliseconds.
        :param rt_draw: Real-time drawing flag.
        :param bt_draw: batch drawing flag.
        :param bt_size: batch drawing size.
        """

        if isinstance(play_speed_ms, int):
            self._player_speed_ms = max(0, min(10000, int(play_speed_ms)))

        if isinstance(rt_draw, bool):
            self.realtime_draw = rt_draw

        if isinstance(bt_draw, bool):
            self.batch_draw = bt_draw
            # Disable real-time drawing when batch drawing is enabled.
            if self.batch_draw:
                self.realtime_draw = False

        if isinstance(bt_size, int):
            self._batch_size = bt_size

        return {"rt": self.realtime_draw, "bt": self.batch_draw, "bs": self._batch_size, "ps": self._player_speed_ms}


    def play(self, animation=None, speed_ms=None, rt_draw=True, bt_draw=False, bt_size=None):
        """
        Play animation via generator function.
        :param animation: Animation generator function.
        :param speed_ms: Speed of the animation in milliseconds. (min.: 3ms)
        :param rt_draw: Real-time drawing flag.
        :param bt_draw: batch drawing flag.
        :param bt_size: batch drawing size.
        """

        if animation is not None:
            if not self._set_animation(animation):
                return "Invalid animation"

        if self.animation is None:
            return "No animation to play"

        # Handle player settings
        self.control(play_speed_ms=speed_ms, rt_draw=rt_draw, bt_draw=bt_draw, bt_size=bt_size)

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
        try:
            self.clear()
        except:
            pass
        return "Stop animation player"

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
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

    def _coord_to_index(self, x: int, y: int):
        """
        Zigzag layout: even rows left-to-right, odd rows right-to-left
        """
        if y % 2 == 0:
            return y * self.width + x
        return y * self.width + (self.width - 1 - x)

    def _rgb_to_grb_with_br(self, color: tuple[int, int, int]):
        """
        Converts RGB to GRB with brightness adjustment.
        """
        def scale(val):
            return max(0, min(255, int(val * self._brightness)))

        return scale(color[1]), scale(color[0]), scale(color[2])

    def set_pixel(self, x: int, y: int, color: tuple[int, int, int]):
        """
        Set pixel at (x, y) with RGB
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            index = self._coord_to_index(x, y)
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
        if manage_task(f"{self._main_tag}.player", "isbusy"):
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


def player_control(speed_ms=None, rt_draw:bool=None, bt_draw:bool=None):
    """
    Change the speed of frame generation for animations.
    """
    data = load().control(play_speed_ms=speed_ms, rt_draw=rt_draw, bt_draw=bt_draw)
    _speed_ms = data.get("ps", None)
    return f"Control state: {data} (speed: {_speed_ms}ms)"


def stop():
    """
    Stop the current animation
    """
    return load().stop()

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

    return load().play(effect_rainbow, speed_ms=speed_ms, rt_draw=False, bt_draw=True, bt_size=8)


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
                             'COLOR color_fill r=<0-255-5> g=<0-255-5> b=<0-255-5>',
                             'SLIDER brightness br=<0-60-2>',
                             'BUTTON stop',
                             'BUTTON snake speed_ms=50 length=5',
                             'BUTTON rainbow',
                             'BUTTON cube speed_ms=10',
                             'SLIDER player_control speed_ms=<2-200-2> rt_draw=None bt_draw=None'), widgets=widgets)
