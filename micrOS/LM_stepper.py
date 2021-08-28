# Based on ULN2003 driver lib: https://github.com/zhcong/ULN2003-for-ESP32

from time import sleep_ms
from machine import Pin
from LogicalPins import physical_pin
STEPPER_INST = None


class StepperULN2003:
    FULL_ROTATION = int(4075.7728395061727 / 8)  # http://www.jangeox.be/2013/10/stepper-motor-28byj-48_25.html

    def __init__(self, mode):
        # Mode: FULL / HALF
        if mode == 'FULL':
            # FULL STEP - ~508
            self.mode = [[1, 0, 1, 0],
                         [0, 1, 1, 0],
                         [0, 1, 0, 1],
                         [1, 0, 0, 1]]
            self.delay = 10
        else:
            # HALF STEP - ~1016
            self.mode = [[0, 0, 0, 1],
                         [0, 0, 1, 1],
                         [0, 0, 1, 0],
                         [0, 1, 1, 0],
                         [0, 1, 0, 0],
                         [1, 1, 0, 0],
                         [1, 0, 0, 0],
                         [1, 0, 0, 1]]
            self.delay = 2
        # Init stepper pins
        self.pin1 = Pin(physical_pin('stppr_1'), Pin.OUT)
        self.pin2 = Pin(physical_pin('stppr_2'), Pin.OUT)
        self.pin3 = Pin(physical_pin('stppr_3'), Pin.OUT)
        self.pin4 = Pin(physical_pin('stppr_4'), Pin.OUT)
        # Initialize all value to 0 - "OFF"
        self.reset()

    def step(self, count, direction=1):
        """Rotate count steps. direction = -1 means backwards"""
        if count < 0:
            direction = -1
            count = -count
        for x in range(count):
            for bit in self.mode[::direction]:
                self.pin1(bit[0])
                self.pin2(bit[1])
                self.pin3(bit[2])
                self.pin4(bit[3])
                sleep_ms(self.delay)
        self.reset()

    def angle(self, r, direction=1):
        self.step(int(self.FULL_ROTATION * r / 360), direction)

    def reset(self):
        # Reset to 0, no holding, these are geared, you can't move them
        self.pin1(0)
        self.pin2(0)
        self.pin3(0)
        self.pin4(0)

    @property
    def speed_ms(self):
        return self.delay

    @speed_ms.setter
    def speed_ms(self, ms):
        # HALF STEP - delay check
        if len(self.mode) > 4 and ms < 1:
            ms = 1
        # FULL STEP - delay check
        elif ms < 10:
            ms = 10
        self.delay = ms


def __init_stepper(mode='HALF'):
    global STEPPER_INST
    if STEPPER_INST is None:
        STEPPER_INST = StepperULN2003(mode)
    return STEPPER_INST


def angle(dg, dr=1, speed=None):
    i = __init_stepper()
    if speed:
        i.speed_ms = speed
    i.angle(dg, dr)
    return "Move {} degree ({},{})".format(dg, i.speed_ms, dr)


def step(st, dr=1, speed=None):
    i = __init_stepper()
    if speed:
        i.speed_ms = speed
    i.step(st, dr)
    return "Move {} step ({},{})".format(st, i.speed_ms, dr)


def standby():
    __init_stepper().reset()
    return "Standby"


def help():
    return 'angle dg=360 dr=<+/-1> speed=<ms>',\
           'step st=2 dr=+/-1 speed=<ms>',\
           'standby',\
           'Info: stepper: 28byj-48 driver: ULN2003'