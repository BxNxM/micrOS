from threading import Event, Lock, Thread, current_thread
import time
import micropython
from sim_common import console


def machine(*args, **kwargs):
    console('machine dummy')
    return 'machine dummy'


class Timer:
    PERIODIC = "DUMMY"
    ONE_SHOT = "ONE_SHOT"

    def __init__(self, timid=0, *args, **kwargs):
        self.timid = timid
        self.thread = None
        self.period_sec = 1
        self.callback = None
        self.mode = self.PERIODIC
        self._lock = Lock()
        self._stop_event = Event()
        self._generation = 0
        console("[Timer - {}] constructor".format(self.timid))

    def init(self, period, mode, callback, *args, **kwargs):
        console("[Timer - {}] init".format(self.timid))
        console("period: {}, mode: {}, callback: {}".format(period, mode, callback))
        if callback is None:
            raise TypeError("Timer callback must not be None")

        self.deinit()

        period_sec = max(float(period) / 1000, 0.001)
        stop_event = Event()
        with self._lock:
            self.period_sec = period_sec
            self.callback = callback
            self.mode = mode
            self._stop_event = stop_event
            self._generation += 1
            generation = self._generation
            self.thread = Thread(
                target=self.__thread,
                args=(stop_event, generation),
                daemon=True,
                name="micrOS-sim-timer-{}-{}".format(self.timid, generation)
            )
            thread = self.thread
        thread.start()

    def deinit(self):
        with self._lock:
            thread = self.thread
            stop_event = self._stop_event
            period_sec = self.period_sec
            self.thread = None
            self.callback = None
            self._generation += 1

        stop_event.set()
        if thread is not None and thread.is_alive() and thread is not current_thread():
            thread.join(timeout=max(period_sec, 0.1) + 0.1)
        console("[Timer - {}] deinit".format(self.timid))
        return True

    def __thread(self, stop_event, generation):
        while True:
            with self._lock:
                period_sec = self.period_sec

            if stop_event.wait(period_sec):
                break

            with self._lock:
                if stop_event.is_set() or generation != self._generation:
                    break
                callback = self.callback
                mode = self.mode

            if callback is None:
                break

            console("\t| thread --[{}s] {}".format(period_sec, callback))
            try:
                output = callback(self)
            except Exception as e:
                console("[Timer - {}] callback error: {}".format(self.timid, e))
                break
            console("\t|--> {}\n".format(output), end='\r')
            micropython.mem_info()

            if mode == self.ONE_SHOT:
                break

        with self._lock:
            if generation == self._generation and self.thread is current_thread():
                self.thread = None
                self.callback = None


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
        self._lock = Lock()

    def irq(self, pin=0, *args, **kwargs):
        with self._lock:
            self.pin = pin
            current_pin = self.pin
        console("[Pin - {}] Set event IRQ".format(current_pin))

    def value(self, value=None):
        with self._lock:
            if value is not None:
                self.__value = value
                action = "SET"
            else:
                action = "GET"
            pin = self.pin
            current_value = self.__value
        console("[Pin - {}] {} value: {}".format(pin, action, current_value), end='\r')
        return current_value

    def deinit(self):
        with self._lock:
            pin = self.pin
        console("[Pin - {}] Deinit obj".format(pin))


class RTC:

    def __init__(self, *args, **kwargs):
        console("[RTC] constructor")

    def datetime(self, *args, **kwargs):
        console("[RTC] datetime")


class WDT:

    def __init__(self, timeout):
        self.timeout = timeout
        self._lock = Lock()
        self._metrics = {
            "last": time.monotonic(),
            "min": 0,
            "max": 0,
            "avg": 0,
            "count": 0,
            "dt": 0
        }

    def feed(self):
        now = time.monotonic()
        with self._lock:
            delta = now - self._metrics["last"]
            self._metrics["last"] = now
            self._metrics["dt"] = delta
            self._metrics["count"] += 1

            if self._metrics["count"] == 1:
                self._metrics["min"] = delta
                self._metrics["max"] = delta
                self._metrics["avg"] = delta
            else:
                self._metrics["min"] = min(self._metrics["min"], delta)
                self._metrics["max"] = max(self._metrics["max"], delta)
                count = self._metrics["count"]
                self._metrics["avg"] = (((self._metrics["avg"] * (count - 1)) + delta) / count)
            metrics = dict(self._metrics)

        if metrics["count"] == 10 or metrics["count"] % 50 == 0:
            console((
                f"[WDT.feed] timeout={self.timeout/1000}s "
                f"count={metrics['count']} "
                f"dt={metrics['dt'] * 1000:.1f}ms "
                f"min={metrics['min'] * 1000:.1f}ms "
                f"max={metrics['max'] * 1000:.1f}ms "
                f"avg={metrics['avg'] * 1000:.1f}ms"
            ))


class PWM:

    def __init__(self, dimmer_pin=None, freq=480):
        self.dimmer_pin = dimmer_pin
        self.__duty = 0
        self.__freq = freq
        self._lock = Lock()
        console("[PWM - {}] {} Hz constructor".format(self.dimmer_pin, self.__freq))

    def duty(self, value=None):
        with self._lock:
            if value is not None:
                self.__duty = value
            duty = self.__duty
        console("[PWM - {}] SET duty: {}".format(self.dimmer_pin, duty))
        return duty

    def freq(self, value=None):
        with self._lock:
            if value is not None:
                self.__freq = value
            freq = self.__freq
        console("[PWM - {}] set freq: {}".format(self.dimmer_pin, freq))
        return freq

    def deinit(self):
        return True


class ADC:
    ATTN_11DB = 'dummy'
    WIDTH_9BIT = 'dummy'
    WIDTH_10BIT = 'dummy'

    def __init__(self, pin=None):
        self.pin = pin
        self.value = self.__gen()
        self._lock = Lock()

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
        with self._lock:
            return self.value.__next__()

    def read_u16(self):
        with self._lock:
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

    def writevto(self, *args, **kwargs):
       pass


class SoftSPI:
    def __init__(self, sck, mosi, miso):
        pass


class UART:

    def __init__(self, pin, baudrate, tx, rx, timeout=1):
        pass

    def init(self, *args, **kwargs):
        pass

    def deinit(self):
        pass

    def write(self, frame):
        pass

    def read(self, *args, **kwargs):
        pass

    def any(self):
        return False

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
