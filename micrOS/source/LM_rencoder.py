import machine
import utime as time
from machine import Pin
import micropython
from Common import socket_stream
from Debug import errlog_add
from LogicalPins import physical_pin, pinmap_dump

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
            errlog_add("Rotary err: {}".format(e))

    def add_handler(self, handler):
        self.handlers.append(handler)

    def call_handlers(self, type):
        for handler in self.handlers:
            handler(type)


class Data:
    ROTARY_OBJ = None
    VAL = 0
    EVENT = True


def _rotary_changed(change):
    if change == Rotary.ROT_CW:
        Data.EVENT = True
        Data.VAL = Data.VAL + 1
    elif change == Rotary.ROT_CCW:
        Data.EVENT = True
        Data.VAL = Data.VAL - 1


def load_n_init():
    """
    Create rotary encoder
    """
    if Data.ROTARY_OBJ is None:
        # GPIO Pins 33 and 35 are for the encoder pins.
        Data.ROTARY_OBJ = Rotary(physical_pin('rot_dt'), physical_pin('rot_clk'))
        Data.VAL = 0
        Data.ROTARY_OBJ.add_handler(_rotary_changed)
    return 'Init RotaryEncoder with IRQs.'


@socket_stream
def read_state(msgobj=None):
    """
    Read rotary encoder status / relative position
    """
    load_n_init()
    if msgobj is not None:
        if Data.EVENT:
            msgobj("[stream] RotaryState: {}".format(Data.VAL))
            Data.EVENT = False
    else:
        return "RotaryState: {}".format(Data.VAL)
    return ""


def reset_state():
    """
    Reset rotary encoder state to 0
    """
    msg = "Reset state {} -> 0".format(Data.VAL)
    Data.VAL = 0
    return msg


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_dump(['rot_clk', 'rot_dt'])


def help():
    return 'load_n_init', 'read_state', 'reset_state', 'pinmap'
