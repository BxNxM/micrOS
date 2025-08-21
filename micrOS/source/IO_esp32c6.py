from micropython import const

"""
[BETA version]
Fucked up pinout, but thanks to
https://docs.cirkitdesigner.com/component/fb9bd4d6-797c-4836-b41b-663033d7fd47/seeed-studio-xiao-esp32c6
    **
3	D0	Digital I/O Pin 0
4	D1	Digital I/O Pin 1
5	D2	Digital I/O Pin 2
6	D3	Digital I/O Pin 3
7	D4	Digital I/O Pin 4
8	D5	Digital I/O Pin 5
9	D6	Digital I/O Pin 6
10	D7	Digital I/O Pin 7
11	D8	Digital I/O Pin 8
12	D9	Digital I/O Pin 9
13	D10	Digital I/O Pin 10

20	RX	UART Receive Pin
21	TX	UART Transmit Pin
22	SCL	I2C Clock Pin
23	SDA	I2C Data Pin
"""

# BUILTIN LED
builtin = const(-15)    # BUILT IN LED - progress_led


# I2C BUS
i2c_sda = const(7)      # D4 - data
i2c_scl = const(8)      # D5 - clock


# EXTERNAL EVENT IRQ
irq1 = const(6)         # D3 - event irq1 pin
irq2 = const(5)         # D2 - event irq2 pin
irq3 = const(4)         # D1 - event irq3 pin
irq4 = const(3)         # D0 - event irq4 pin


neop = const(13)        # D10 - neopixel OneWire bus [PWM]

