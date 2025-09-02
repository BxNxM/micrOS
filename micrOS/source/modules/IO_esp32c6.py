from micropython import const

"""
Seeed Studio XIAO ESP32-C6

BOARD        MICROPYTHON
D0/A0    -   GPIO 0
D1/A1    -   GPIO 1
D2/A2    -   GPIO 2
D3       -   GPIO 21
D4 SDA   -   GPIO 22
D5 SCL   -   GPIO 23
D6 TX0   -   GPIO 16
D7 RX0   -   GPIO 17
D8 SCK   -   GPIO 19
D9 MISO  -   GPIO 20
D10 MOSI -   GPIO 18
BUILTIN LED - GPIO 15
"""

# BUILTIN LED
builtin = const(-15)     # BUILT IN LED - progress_led


# I2C BUS
i2c_sda = const(22)      # D4 - data
i2c_scl = const(23)      # D5 - clock


# EXTERNAL EVENT IRQ
irq1 = const(21)         # D3 - event irq1 pin
irq2 = const(2)          # D2 - event irq2 pin
irq3 = const(1)          # D1 - event irq3 pin
irq4 = const(0)          # D0 - event irq4 pin


neop = const(18)         # D10 - neopixel OneWire bus [PWM]

