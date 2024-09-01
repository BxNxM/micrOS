"""
trackball.py - MicroPython module Pimoroni trackball breadkout.
Based on https://github.com/mchobby/esp8266-upy/blob/master/trackball/lib/trackball.py
* MicroPython standard API
https://github.com/mchobby/esp8266-upy/blob/master/trackball/examples/test_colorcontrol.py
"""

import time
import struct
from machine import I2C, Pin
from microIO import resolve_pin
from Common import syslog
from random import randint

TRACKBALL = None

#############################
#       Trackball core      #
#############################

CHIP_ID = 0xBA11

REG_LED_RED = 0x00
REG_LED_GRN = 0x01
REG_LED_BLU = 0x02
REG_LED_WHT = 0x03

REG_LEFT = 0x04
REG_RIGHT = 0x05
REG_UP = 0x06
REG_DOWN = 0x07
REG_SWITCH = 0x08
MSK_SWITCH_STATE = 0b10000000

REG_USER_FLASH = 0xD0
REG_FLASH_PAGE = 0xF0
REG_INT = 0xF9
MSK_INT_TRIGGERED = 0b00000001
MSK_INT_OUT_EN = 0b00000010
REG_CHIP_ID_L = 0xFA
RED_CHIP_ID_H = 0xFB
REG_VERSION = 0xFC
REG_I2C_ADDR = 0xFD
REG_CTRL = 0xFE
MSK_CTRL_SLEEP = 0b00000001
MSK_CTRL_RESET = 0b00000010
MSK_CTRL_FREAD = 0b00000100
MSK_CTRL_FWRITE = 0b00001000


class Trackball:
    EVENT_LISTENERS = []

    def __init__(self, i2c, address=0x0A, max_x=100, max_y=100):
        self.address = address
        self.i2c = i2c
        self._max_x = max_x
        self._max_y = max_y
        self.posx = 0
        self.posy = 0
        self.toggle = False
        self.action = None

        data = self.i2c.readfrom_mem( self.address, REG_CHIP_ID_L, 2 )
        chip_id = struct.unpack("<H", data)[0]
        if chip_id != CHIP_ID:
            raise Exception("Invalid chip ID: 0x{:04X}, expected 0x{:04X}".format(chip_id, CHIP_ID))
        self.enable_interrupt()

    def enable_interrupt(self, interrupt=True):
        """ Enable/disable GPIO interrupt pin on the breakout."""
        value = self.i2c.readfrom_mem( self.address, REG_INT, 1)[0]
        value = value & (0xFF ^ MSK_INT_OUT_EN)
        if interrupt:
            value = value | MSK_INT_OUT_EN
        self.i2c.writeto_mem( self.address, REG_INT, bytes([value]) )

    def get_interrupt(self):
        """Get the trackball interrupt status."""
        # Only support the software version
        data = self.i2c.readfrom_mem( self.address, REG_INT, 1)
        return (data[0] & MSK_INT_TRIGGERED)==MSK_INT_TRIGGERED

    def set_rgbw(self, r, g, b, w):
        """Set all LED brightness as RGBW."""
        self.i2c.writeto_mem( self.address, REG_LED_RED, bytes([r, g, b, w]) )

    def set_red(self, value):
        """Set brightness of trackball red LED."""
        self.i2c.writeto_mem( self.address, REG_LED_RED, bytes([value & 0xff]) )

    def set_green(self, value):
        """Set brightness of trackball green LED."""
        self.i2c.writeto_mem( self.address, REG_LED_GRN, bytes([value & 0xff]) )

    def set_blue(self, value):
        """Set brightness of trackball blue LED."""
        self.i2c.writeto_mem( self.address, REG_LED_BLU, bytes([value & 0xff]) )

    def set_white(self, value):
        """Set brightness of trackball white LED."""
        self.i2c.writeto_mem( self.address, REG_LED_WHT, bytes([value & 0xff]) )

    def _state_machine(self, up, down, left, right, state):
        # Update cursor positions
        self.posy += up - down
        self.posx += right - left
        self.posx = max(0, min(self.posx, self._max_x))
        self.posy = max(0, min(self.posy, self._max_y))
        if state != self.toggle:
            self.toggle = not self.toggle
            self.action = "center"
            time.sleep(0.5)     # Avoid bouncing
        else:
            d = {'up': up, 'down': down, 'left': left, 'right': right}
            if sum((abs(i) for i in d.values())) > 0:
                self.action = max(d, key=d.get)

    def read(self):
        """Read up, down, left, right and switch data from trackball."""
        data = self.i2c.readfrom_mem( self.address, REG_LEFT, 5 )
        left, right, up, down, switch = data[0], data[1], data[2], data[3], data[4]
        switch, switch_state = switch & (0xFF ^ MSK_SWITCH_STATE), (switch & MSK_SWITCH_STATE)==MSK_SWITCH_STATE
        self._state_machine(up, down, left, right, switch_state)
        return up, down, left, right, switch, switch_state



def load(width=100, height=100):
    """
    Load Pimoroni trackball
    """
    global TRACKBALL
    if TRACKBALL is None:
        i2c = I2C(scl=Pin(resolve_pin('i2c_scl')), sda=Pin(resolve_pin('i2c_sda')))
        TRACKBALL = Trackball(i2c, max_x=width, max_y=height)
        _event_interrupt()
    return TRACKBALL


def settings():
    "Get simple trackball settings"
    tb = load()
    return {"width": tb._max_x, "height": tb._max_y, "irq": tb.get_interrupt(), "addr": tb.address}


def _event_interrupt():
    """
    Handle hange events from trackball
    """
    def _callback():
        # Update trackball data
        load().read()
        # Execute callbacks
        try:
            for clbk in Trackball.EVENT_LISTENERS:
                if callable(clbk):
                    clbk(get())
        except:
            syslog("Trackball callback event error")

    try:
        pin = resolve_pin("trackball_int")
    except Exception as e:
        pin = None
        syslog(f'[ERR] trackball_int IRQ: {e}')
    if pin:
        pin_obj = Pin(pin, Pin.IN, Pin.PULL_DOWN)
        # [IRQ] - event type setup
        pin_obj.irq(trigger=Pin.IRQ_RISING, handler=_callback)



def read():
    """
    Read trackball data over i2c
    """
    trackball = load()
    trackball.read()
    # Set LEDs
    trackball.set_rgbw(r=randint(0,100), g=randint(0,100), b=randint(0, 100), w=0)

    return {"X": trackball.posx, "Y": trackball.posy,
            "S": trackball.toggle, "action": trackball.action}


def get():
    """
    Get up-to-date (by irq) data
    """
    trackball = load()
    return {"X": trackball.posx, "Y": trackball.posy,
            "S": trackball.toggle, "action": trackball.action}


def subscribe_event(func):
    """
    Add callback function to trackball events
    """
    if func not in EVENT_LISTENERS:
        Trackball.EVENT_LISTENERS.append(func)


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pinmap_search(['i2c_scl', 'i2c_sda', 'trackball_int'])


def help():
    return "load width=100 height=100", "read", "get", "settings", "pinmap"
