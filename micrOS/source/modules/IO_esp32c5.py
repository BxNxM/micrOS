from micropython import const

#### DEFINE CUSTOM PROGRESS LED LOGIC ####
class WS2812:
    NEOPIXEL = None
    WHEEL = None
    PIN = const(27)                         # BUILT IN LED - progress_led

try:
    # init ws2812
    from machine import Pin
    from neopixel import NeoPixel
    WS2812.NEOPIXEL = NeoPixel(Pin(WS2812.PIN), 1)
except Exception as e:
    print(f"[Error] IO error, esp21se ws2812: {e}")


def _step_ws2812(pin=False):
    if pin:
        return WS2812.PIN

    def _color_wheel():
        while True:
            yield 10, 0, 0
            yield 5, 5, 0
            yield 0, 10, 0
            yield 0, 5, 5
            yield 0, 0, 10
            yield 5, 0, 5

    if WS2812.WHEEL is None:
        WS2812.WHEEL = _color_wheel()
    WS2812.NEOPIXEL[0] = next(WS2812.WHEEL)
    WS2812.NEOPIXEL.write()
    return True  # No double-blink

#######################################

# BUILTIN LED
builtin = _step_ws2812     # BUILT IN LED - progress_led


# I2C BUS
i2c_sda = const(6)      # serial data
i2c_scl = const(7)      # serial clock


# EXTERNAL EVENT IRQ
irq1 = const(24)         # event irq1 pin
irq2 = const(23)         # event irq2 pin
irq3 = const(15)         # event irq3 pin
irq4 = const(10)         # event irq4 pin


neop = const(25)         # D10 - neopixel OneWire bus [PWM]
