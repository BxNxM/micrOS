from machine import Pin
import micropython
from Common import socket_stream, syslog
from microIO import bind_pin, pinmap_search
from Types import resolve

# https://www.coderdojotc.org/micropython/sensors/10-rotary-encoder/


class Rotary:
    ROT_CW = 1
    ROT_CCW = 2

    def __init__(self, dt, clk):
        self.dt_pin = Pin(dt, Pin.IN, Pin.PULL_DOWN)
        self.clk_pin = Pin(clk, Pin.IN, Pin.PULL_DOWN)
        self.last_status = (self.dt_pin.value() << 1) | self.clk_pin.value()
        self.dt_pin.irq(handler=self.rotary_change, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)
        self.clk_pin.irq(handler=self.rotary_change, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)
        self.handlers = []

    def rotary_change(self, pin):
        new_status = (self.dt_pin.value() << 1) | self.clk_pin.value()
        if new_status == self.last_status:
            return
        transition = (self.last_status << 2) | new_status
        try:
            if transition == 0b1110:
                micropython.schedule(self.call_handlers, Rotary.ROT_CW)
            elif transition == 0b1101:
                micropython.schedule(self.call_handlers, Rotary.ROT_CCW)
            self.last_status = new_status
        except Exception as e:
            syslog(f"Rotary err: {e}")

    def add_handler(self, handler):
        self.handlers.append(handler)

    def call_handlers(self, type):
        for handler in self.handlers:
            handler(type)


class Data:
    ROTARY_OBJ = None
    EVENT = True
    VAL = 0
    MIN_VAL = 0
    MAX_VAL = 20
    COLOR = (None, ())


def _rotary_changed(change):
    if change == Rotary.ROT_CW:
        Data.EVENT = True
        Data.VAL = Data.VAL + 1
        if Data.VAL > Data.MAX_VAL:
            Data.VAL = Data.MIN_VAL
    elif change == Rotary.ROT_CCW:
        Data.EVENT = True
        Data.VAL = Data.VAL - 1
        if Data.VAL < Data.MIN_VAL:
            Data.VAL = Data.MAX_VAL
    # Color on neopixel
    if callable(Data.COLOR[0]):
        try:
            r, g, b = Data.COLOR[1][Data.VAL]
            Data.COLOR[0](r, g, b)
        except Exception as e:
            syslog(f"[ERR] rencoder color: {e}")


def load(min_val=0, max_val=20):
    """
    Create rotary encoder
    """
    if Data.ROTARY_OBJ is None:
        # GPIO Pins 33 and 35 are for the encoder pins.
        Data.ROTARY_OBJ = Rotary(bind_pin('rot_dt'), bind_pin('rot_clk'))
        Data.MIN_VAL = min_val
        Data.MAX_VAL = max_val
        Data.VAL = min_val
        Data.ROTARY_OBJ.add_handler(_rotary_changed)
    return 'Init RotaryEncoder with IRQs.'


@socket_stream
def read_state(msgobj=None):
    """
    Read rotary encoder status / relative position
    """
    load()
    if msgobj is not None:
        if Data.EVENT:
            msgobj(f"[stream] RotaryState: {Data.VAL}")
            Data.EVENT = False
    else:
        return f"RotaryState: {Data.VAL}"
    return ""


def reset_state():
    """
    Reset rotary encoder state to 0
    """
    msg = f"Reset state {Data.VAL} -> 0"
    Data.VAL = Data.MIN_VAL
    return msg


def pinmap():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application (widgets=False)
    :return tuple: list of widget json for UI generation (widgets=True)
    """
    return pinmap_search(['rot_clk', 'rot_dt'])


def color_indicator():
    """Encoder visualization on LED colors (LM_neopixel)"""
    from LM_neopixel import color
    palette_template = ((20, 0, 0), (10, 10, 0), (0, 20, 0), (0, 10, 10), (0, 0, 20))
    repeat = int(Data.MAX_VAL / len(palette_template))+1
    palette = palette_template * repeat
    Data.COLOR = (color, palette)
    color(0, 0, 0)          # initial color OFF
    return palette


def help(widgets=False):
    return resolve(('load min_val=0 max_val=20', 'TEXTBOX read_state',
                             'reset_state', 'color_indicator', 'pinmap'), widgets=widgets)
