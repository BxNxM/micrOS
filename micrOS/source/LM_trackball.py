"""
trackball.py - MicroPython module Pimoroni trackball breadkout.
Based on https://github.com/mchobby/esp8266-upy/blob/master/trackball/lib/trackball.py
* MicroPython standard API
https://github.com/mchobby/esp8266-upy/blob/master/trackball/examples/test_colorcontrol.py
"""

from utime import sleep, ticks_ms, ticks_diff
from struct import unpack
from machine import SoftI2C, Pin
from microIO import resolve_pin, pinmap_search
from Common import syslog
from micropython import schedule

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

    def __init__(self, i2c, address=0x0A, max_x=100, max_y=100, sensivity=1, upscale=2):
        self.address = address
        self.i2c = i2c
        self._max_x = max_x
        self._max_y = max_y
        self.posx = 0
        self.posy = 0
        self.toggle = False
        self.action = None
        self.sensivity = sensivity
        self.upscale = upscale
        self._last_event = ticks_ms()
        self._last_event_coords = (self.posx, self.posy)

        data = self.i2c.readfrom_mem( self.address, REG_CHIP_ID_L, 2 )
        chip_id = unpack("<H", data)[0]
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

    def auto_color(self):
        if self.action == "press":
            w_br, x_br, y_br = 50, 0, 0
        else:
            w_br = 0
            x_br = int(100 * (self.posx / self._max_x))
            y_br = int(100 * (self.posy / self._max_y))
        self.set_rgbw(r=y_br, g=3, b=x_br, w=w_br)

    def detection_block(self, window=5):
        window = window*self.upscale
        # Experimental - dymaic sampling time sensitivity...
        last_x, last_y = self._last_event_coords
        if abs(self.posx - last_x) > window or abs(self.posy - last_y) > window:
            return True
        return False

    def _state_machine(self, up, down, left, right, state):
        # Update cursor positions
        change_x = (right - left)
        change_y = (up - down)
        self.posx += change_x * self.upscale
        self.posy += change_y * self.upscale
        self.posx = max(0, min(self.posx, self._max_x))
        self.posy = max(0, min(self.posy, self._max_y))
        # Check sensitivity
        delta_t = ticks_diff(ticks_ms(), self._last_event)
        if delta_t > self.sensivity or detection_block():
            self._last_event = ticks_ms()
            if state != self.toggle:
                self.toggle = not self.toggle
                self.action = "press"
                sleep(0.2)     # Avoid bouncing
            else:
                d = {'up': up, 'down': down, 'left': left, 'right': right}
                if sum((abs(i) for i in d.values())) > 0:
                    self.action = max(d, key=d.get)
            self._last_event_coords = self.posx, self.posy
            return True
        return False

    def read(self):
        """Read up, down, left, right and switch data from trackball."""
        data = self.i2c.readfrom_mem( self.address, REG_LEFT, 5 )
        left, right, up, down, switch = data[0], data[1], data[2], data[3], data[4]
        switch, switch_state = switch & (0xFF ^ MSK_SWITCH_STATE), (switch & MSK_SWITCH_STATE)==MSK_SWITCH_STATE
        trigger = self._state_machine(up, down, left, right, switch_state)
        return up, down, left, right, switch, switch_state, trigger



def load(width=100, height=100, sensivity=20, reload=False):
    """
    Load Pimoroni trackball
    :param width: canvas pixel width
    :param height: canvas pixel height
    :param sensivity: trackball sensivity in ms
    :param reload: recreate trackball instance
    """
    global TRACKBALL
    if TRACKBALL is None or reload:
        i2c = SoftI2C(scl=Pin(resolve_pin('i2c_scl')), sda=Pin(resolve_pin('i2c_sda')))
        TRACKBALL = Trackball(i2c, max_x=width, max_y=height, sensivity=sensivity)
        _event_interrupt()
        TRACKBALL.set_green(10)
    return TRACKBALL


def settings(sensivity=None):
    """
    Get simple trackball settings
    :param sensivity: optional param, change sensivity ms
    """
    tb = load()
    if isinstance(sensivity, int):
        tb.sensivity = sensivity
    return {"width": tb._max_x, "height": tb._max_y, "irq": tb.get_interrupt(),
            "addr": hex(tb.address), "sensivity": tb.sensivity}


def read():
    """
    Read trackball data over i2c
    """
    trackball = load()
    up, down, left, right, switch, switch_state, trigger = trackball.read()
    if trigger:
        trackball.auto_color()
    return {"X": trackball.posx, "Y": trackball.posy,
            "S": trackball.toggle, "action": trackball.action}


def get():
    """
    Get up-to-date (by irq) data
    """
    trackball = load()
    return {"X": trackball.posx, "Y": trackball.posy,
            "S": trackball.toggle, "action": trackball.action}


def _event_interrupt():
    """
    Handle hange events from trackball
    """
    def _callback(pin):
        # Update trackball data
        trackball = load()
        up, down, left, right, switch, switch_state, trigger = trackball.read()
        if trigger:
            trackball.auto_color()
            # Execute callbacks
            for clbk in Trackball.EVENT_LISTENERS:
                if callable(clbk):
                    try:
                        clbk(get())
                    except:
                        syslog(f"Trackball callback event error: {pin}")

    try:
        pin = resolve_pin("trackball_int")
    except Exception as e:
        pin = None
        syslog(f'[ERR] trackball_int IRQ: {e}')
    if pin:
        pin_obj = Pin(pin, Pin.IN, Pin.PULL_DOWN)
        pin_obj.irq(trigger=Pin.IRQ_FALLING, handler=lambda pin: schedule(_callback, pin))


def subscribe_event(func):
    """
    Add callback function to trackball events
    """
    if func not in Trackball.EVENT_LISTENERS:
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
    return "load width=100 height=100 sensivity=20", "read", "get", "settings sensivity=None", "pinmap"
