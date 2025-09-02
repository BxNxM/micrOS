from micropython import const

#### DEFINE CUSTOM PROGRESS LED LOGIC ####
class WS2812:
    NEOPIXEL = None
    WHEEL = None
    PIN = const(5)                                      # BUILT IN LED - progress_led
    PIN_ENABLE = const(8)                               # Power ON LED

try:
    # init ws2812
    from neopixel import NeoPixel
    from machine import Pin
    Pin(WS2812.PIN_ENABLE, Pin.OUT).value(1)            # Power ON LED
    WS2812.NEOPIXEL = NeoPixel(Pin(WS2812.PIN), 1)      # BUILT IN LED - progress_led
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

###########################################

# BUILTIN LED
builtin = _step_ws2812


# ANALOG RGB + WW + CW
redgb = const(26)      # A0 - rgb red channel [PWM]
rgreenb = const(25)    # A1 - rgb green channel [PWM]
rgbue = const(27)      # A2 - rgb blue channel [PWM]

wwhite = const(12)	   # MI - warm white [PWM]
cwhite = const(13)	   # MO - cold white [PWM]


# DIGITAL LED
neop = const(15)       # A3 - neopixel OneWire bus [PWM]


# ACTUATORS
servo_1 = const(26)    # A0 - servo(1) [PWM]
servo_2 = const(25)    # A1 - servo(2) [PWM]

switch_1 = const(13)   # MO - switch(1) [simple]
switch_2 = const(12)   # MI - switch(2) [simple]
switch_3 = const(14)   # SCK - switch(3) [simple]
switch_4 = const(7)    # RX - switch(4) [simple]

dim_1 = const(32)      # TX - dimmer(1) [PWM]

buzzer = const(26)     # A0 - Buzzer pin - sound generator

# I2C BUS
i2c_sda = const(4)    # D22 - oled - data
i2c_scl = const(33)   # D21 - oled - clock
# I2S BUS
i2s_sck = const(26)    # Serial clock
i2s_ws = const(25)     # Word select
i2s_sd = const(33)     # Serial data


# EXTERNAL EVENT IRQ
irq1 = const(13)         # MO  - event irq pin
irq2 = const(12)         # MI - event irq pin
irq3 = const(14)         # SCK  - event irq pin
irq4 = const(7)          # TX  - event irq pin

js_right = const(13)      # oled_ui joystick
js_left = const(12)
js_up = const(14)
js_down = const(7)
js_press = const(32)     # oled_ui center/ok button


# SENSORS
dhtpin = const(13)     # MO - dht_pin 11 and 22
co2 = const(25)        # A1 - [ADC] CO2
temp6000 = const(27)   # A2  - [ADC] light sensor TEMP6000
ds18 = const(32)       # TX - DS18B20 - temp. sensor
mic = const(15)        # A3  - [ADC] microphone
