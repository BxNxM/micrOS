from micropython import const

# BUILTIN LED
builtin = const(21)    # BUILT IN LED - progress_led

# ANALOG RGB + WW + CW
redgb = const(43)      # - rgb red channel [PWM]
rgreenb = const(44)    # - rgb green channel [PWM]
rgbue = const(0)      # - rgb blue channel [PWM]

wwhite = const(39)	   # - warm white [PWM]
cwhite = const(40)	   # - cold white [PWM]

# DIGITAL LED
neop = const(0)       # - neopixel OneWire bus [PWM]

# ACTUATORS
servo_1 = const(44)    # - servo(1) [PWM]
servo_2 = const(42)    # - servo(2) [PWM]

switch_1 = const(39)   # - switch(1) [simple]
switch_2 = const(40)   # - switch(2) [simple]
switch_3 = const(41)    # - switch(3) [simple]
switch_4 = const(16)    # - switch(4) [simple]

dim_1 = const(43)      # - dimmer(1) [PWM]

buzzer = const(1)      # - Buzzer pin - sound generator

# I2C BUS
i2c_sda = const(13)    # - oled - data
i2c_scl = const(15)    # - oled - clock
# I2S BUS
i2s_sck = const(5)    # Serial clock
i2s_ws = const(7)     # Word select
i2s_sd = const(9)     # Serial data


# EXTERNAL EVENT IRQ
irq1 = const(15)        # - event irq pin
irq2 = const(13)        # - event irq pin
irq3 = const(14)        # - event irq pin
irq4 = const(12)        # - event irq pin

touch_0 = const(1)     # - touch sensor TODO

# SENSORS
hcsrtrig = const(1)   # - distance HCSR04 trigger pin
hcsrecho = const(3)   # - distance HCSR04 echo pin
dhtpin = const(43)     # - dht_pin 11 and 22
ds18 = const(0)       # - DS18B20 - temp. sensor
mic = const(3)         # - [ADC] microphone
