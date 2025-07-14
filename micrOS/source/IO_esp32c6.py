from micropython import const

# BUILTIN LED
builtin = const(-15)     # BUILT IN LED - progress_led


# I2C BUS
i2c_sda = const(4)    # D21 - oled - data
i2c_scl = const(5)    # D22 - oled - clock


# EXTERNAL EVENT IRQ
irq1 = const(3)         # D4  - event irq pin
irq2 = const(2)        # D18 - event irq pin
irq3 = const(1)         # D19  - event irq pin
irq4 = const(0)        # D13  - event irq pin
