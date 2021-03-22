from threading import Thread
import time
import micropython
from sim_console import console


def machine(*args, **kwargs):
    console('machine dummy')
    return 'machine dummy'


class Timer:
    PERIODIC = "DUMMY"

    def __init__(self, timid=0, *args, **kwargs):
        self.timid = timid
        self.thread = None
        self.period_sec = 1
        self.callback = None
        console("[Timer - {}] constructor".format(self.timid))

    def init(self, period, mode, callback, *args, **kwargs):
        console("[Timer - {}] init".format(self.timid))
        console("period: {}, mode: {}, callback: {}".format(period, mode, callback))
        self.period_sec = period / 1000
        self.callback = callback
        self.thread = Thread(target=self.__thread, daemon=True)
        self.thread.start()

    def __thread(self):
        while True:
            console("\t| thread --[{}s] {}".format(self.period_sec, self.callback))
            output = self.callback(None)
            console("\t|--> {}\n".format(output), end='\r')
            micropython.mem_info()
            time.sleep(self.period_sec)


class Pin:
    IN = 'DUMMY'
    OUT = 'DUMMY'
    PULL_UP = 'DUMMY'
    IRQ_RISING = 'DUMMY'

    def __init__(self, *args, **kwargs):
        console("[Pin] object constructor")
        self.__value = False
        self.pin = None

    def irq(self, pin=0, *args, **kwargs):
        self.pin = pin
        console("[Pin - {}] Set event IRQ".format(self.pin))

    def value(self, value=None):
        if value is None:
            console("[Pin - {}] GET value: {}".format(self.pin, self.__value), end='\r')
            return self.__value
        self.__value = value
        console("[Pin - {}] SET value: {}".format(self.pin, self.__value), end='\r')
        return self.__value

    def deinit(self):
        console("[Pin - {}] Deinit obj".format(self.pin))


class RTC:

    def __init__(self, *args, **kwargs):
        console("[RTC] constructor")

    def datetime(self, *args, **kwargs):
        console("[RTC] datetime")


class PWM:

    def __init__(self, dimmer_pin=None, freq=480):
        self.dimmer_pin = dimmer_pin
        self.__duty = 0
        self.__freq = freq
        console("[PWM - {}] {} Hz constructor".format(self.dimmer_pin, self.__freq))

    def duty(self, value=None):
        if value is not None:
            self.__duty = value
        console("[PWM - {}] SET duty: {}".format(self.dimmer_pin, self.__duty))
        return self.__duty

    def freq(self, value=None):
        if value is not None:
            self.__freq = value
        console("[PWM - {}] set freq: {}".format(self.dimmer_pin, self.__freq))
        return self.__freq


class ADC:
    ATTN_11DB = 'dummy'
    WIDTH_9BIT = 'dummy'

    def __init__(self, pin=None):
        pass

    def atten(self, *args, **kwargs):
        pass

    def width(self, *args, **kwargs):
        pass

    def read(self):
        return 420


def freq(*args, **kwargs):
    pass


def reset():
    print("[SIM] Dummy machine.reset")
    return True


def reset_cause():
    return 0


def unique_id():
    return hex(1234)
