# ULN2003 driver lib: https://github.com/zhcong/ULN2003-for-ESP32

import time
from machine import Pin
STEPPER_INST = None


class StepperULN2003:
    FULL_ROTATION = int(4075.7728395061727 / 8)  # http://www.jangeox.be/2013/10/stepper-motor-28byj-48_25.html

    HALF_STEP = [
        [0, 0, 0, 1],
        [0, 0, 1, 1],
        [0, 0, 1, 0],
        [0, 1, 1, 0],
        [0, 1, 0, 0],
        [1, 1, 0, 0],
        [1, 0, 0, 0],
        [1, 0, 0, 1],
    ]

    FULL_STEP = [
        [1, 0, 1, 0],
        [0, 1, 1, 0],
        [0, 1, 0, 1],
        [1, 0, 0, 1]
    ]

    def __init__(self, mode, pin1, pin2, pin3, pin4, delay):
        if mode == 'FULL_STEP':
            self.mode = self.FULL_STEP
        else:
            self.mode = self.HALF_STEP
        self.pin1 = pin1
        self.pin2 = pin2
        self.pin3 = pin3
        self.pin4 = pin4
        self.delay = delay  # Recommend 10+ for FULL_STEP, 1 is OK for HALF_STEP

        # Initialize all to 0
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
                time.sleep_ms(self.delay)
        self.reset()

    def angle(self, r, direction=1):
        self.step(int(self.FULL_ROTATION * r / 360), direction)

    def reset(self):
        # Reset to 0, no holding, these are geared, you can't move them
        self.pin1(0)
        self.pin2(0)
        self.pin3(0)
        self.pin4(0)


def __init_stepper():
    global STEPPER_INST
    if STEPPER_INST is None:
        STEPPER_INST = StepperULN2003('HALF_STEP',
                          Pin(16, Pin.OUT), Pin(17, Pin.OUT), Pin(5, Pin.OUT), Pin(18, Pin.OUT),
                          delay=2)
    return STEPPER_INST


def angle(dg, dr=1):
    __init_stepper().angle(dg, dr)


def step(st, dr=1):
    __init_stepper().step(st, dr)


def help():
    return 'angle dg=360 dr=1', 'step st=2 dr=1', 'Info: stepper: 28byj-48 driver: ULN2003'
