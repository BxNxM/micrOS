from threading import Thread
import time
import micropython
from sim_console import console
import sys


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
    IN = 0
    OUT = 0
    PULL_UP = 0
    PULL_DOWN = 0
    IRQ_RISING = 0
    IRQ_FALLING = 0

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

    def deinit(self):
        return True


class ADC:
    ATTN_11DB = 'dummy'
    WIDTH_9BIT = 'dummy'
    WIDTH_10BIT = 'dummy'

    def __init__(self, pin=None):
        self.pin = pin
        self.value = self.__gen()

    def __gen(self):
        while True:
            for k in range(0, 65535, 500):
                console(f"ADC({self.pin}): {k}")
                yield k
            for k in range(65535, 0, 500):
                console(f"ADC({self.pin}): {k}")
                yield k

    def atten(self, *args, **kwargs):
        pass

    def width(self, *args, **kwargs):
        pass

    def read(self):
        return self.value.__next__()

    def read_u16(self):
        return self.value.__next__()


class I2C:

    def __init__(self, scl, sda, freq=None):
        self.scl = scl
        self.sda = sda
        self.freq = freq

    def writeto(self, address, value):
        console(f"[I2C writeto] scl: {self.scl} sda: {self.sda} freq: {self.freq} addr: {address} value: {value}")
        return True

    def writeto_mem(self, address, register, b):
        console(f"[I2C writeto_mem] scl: {self.scl} sda: {self.sda} freq: {self.freq} addr: {address} reg: {register} bit: {b}")
        return True

    def readfrom(self, address, byte):
        console(f"[I2C readfrom] scl: {self.scl} sda: {self.sda} freq: {self.freq} addr: {address} byte: {byte}")
        return b'00000000'

    def readfrom_mem(self, address, register, byte):
        console(f"[I2C readfrom_mem] scl: {self.scl} sda: {self.sda} freq: {self.freq} addr: {address} reg: {register} byte: {byte}")
        return b'00000000'

    def scan(self):
        # Test data: trackball, oled
        return [0x0A, 0x3c]


class I2S:
    MONO = 0
    STEREO = 1

    @staticmethod
    def shift(buf, shift, bits):
        console(f"[I2S shift] buf: {buf} shift: {shift} bits: {bits}")
        return None


class SoftI2C(I2C):

    def __init__(self, scl, sda, freq=None):
        super().__init__(scl, sda, freq)


class SoftSPI:
    def __init__(self, sck, mosi, miso):
        pass


class UART:

    def __init__(self, pin, baudrate, tx, rx, timeout=1):
        pass

    def write(self, frame):
        pass

    def read(self, *args, **kwargs):
        pass

def freq(*args, **kwargs):
    return 1


def reset():
    print("[SIM] Dummy machine.reset")
    return True


def soft_reset():
    print("[SIM] Dummy machine.soft_reset")
    return True


def reset_cause():
    return 0


def unique_id():
    return b'08b61f3b6d18'


def time_pulse_us():
    return time.time_ns()*1000


def SDCard():
    pass
