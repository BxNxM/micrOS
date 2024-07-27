from micropython import const

# BUILTIN LED
builtin = const(-8)     # BUILT IN LED - progress_led,  (-) means inverted output

# ANALOG RGB + WW + CW
redgb = const(4)      # - rgb red channel [PWM]
rgreenb = const(3)    # - rgb green channel [PWM]
rgbue = const(2)      # - rgb blue channel [PWM]

wwhite = const(1)	  # - warm white [PWM]
cwhite = const(0)	  # - cold white [PWM]


# DIGITAL LED
neop = const(7)        # - neopixel OneWire bus [PWM]


# ACTUATORS
servo_1 = const(6)      # - servo(1) [PWM]
servo_2 = const(7)      # - servo(2) [PWM]

switch_1 = const(8)     # - switch(1) [simple]
switch_2 = const(9)     # - switch(2) [simple]
switch_3 = const(10)    # - switch(3) [simple]
switch_4 = const(20)    # - switch(4) [simple]

dim_1 = const(21)        # - dimmer(1) [PWM]

buzzer = const(0)        # - Buzzer pin - sound generator

# EXTERNAL EVENT IRQ
irq1 = const(5)          # event irq pin
irq2 = const(6)          # event irq pin
irq3 = const(7)          # event irq pin
irq4 = const(8)          # event irq pin

js_right = const(5)      # oled_ui joystick
js_left = const(6)
js_up = const(7)
js_down = const(8)
js_press = const(20)     # oled_ui center/ok button

# I2C BUS
i2c_sda = const(8)       # oled - data
i2c_scl = const(9)       # oled - clock
# UART BUS
tx = const(21)           # UART - TX
rx = const(20)           # UART - RX

# SENSORS
ds18 = const(10)         # - DS18B20 - temp. sensor
dhtpin = const(2)        # - dht_pin 11 and 22
