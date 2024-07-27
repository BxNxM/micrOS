from micropython import const

# BUILTIN LED
builtin = const(38)     # BUILT IN LED - progress_led

# ANALOG RGB + WW + CW
redgb = const(37)      # - rgb red channel [PWM]
rgreenb = const(36)    # - rgb green channel [PWM]
rgbue = const(35)      # - rgb blue channel [PWM]

wwhite = const(40)	   # - warm white [PWM]
cwhite = const(39)	   # - cold white [PWM]


# DIGITAL LED
neop = const(6)       # - neopixel OneWire bus [PWM]


# ACTUATORS
servo_1 = const(4)    # - servo(1) [PWM]
servo_2 = const(5)    # - servo(2) [PWM]

switch_1 = const(6)   # - switch(1) [simple]
switch_2 = const(7)   # - switch(2) [simple]
switch_3 = const(15)    # - switch(3) [simple]
switch_4 = const(16)    # - switch(4) [simple]

dim_1 = const(17)      # - dimmer(1) [PWM]

l298speed = const(18)  # - DC motor pwm control [PWM]
l298dir_1 = const(8)  # - DC motor direction (1)
l298dir_2 = const(3)  # - DC motor direction (2)

l9110dir_1 = const(46) # - DC motor direction (1)
l9110dir_2 = const(9)  # - DC motor direction (2)

buzzer = const(2)      # - Buzzer pin - sound generator


stppr_1 = const(43)    # - stepper motor pin
stppr_2 = const(44)    # - stepper motor pin
stppr_3 = const(1)     # - stepper motor pin
stppr_4 = const(2)     # - stepper motor pin


# I2C BUS
i2c_sda = const(42)    # - oled - data
i2c_scl = const(41)    # - oled - clock
# I2S BUS
i2s_sck = const(42)    # Serial clock
i2s_ws = const(41)     # Word select
i2s_sd = const(21)     # Serial data


# EXTERNAL EVENT IRQ
irq1 = const(45)        # - event irq pin
irq2 = const(48)        # - event irq pin
irq3 = const(47)        # - event irq pin
irq4 = const(21)        # - event irq pin

js_right = const(45)      # oled_ui joystick
js_left = const(48)
js_up = const(47)
js_down = const(21)
js_press = const(20)     # oled_ui center/ok button

touch_0 = const(0)     # - touch sensor TODO

# SENSORS
hcsrtrig = const(1)   # - distance HCSR04 trigger pin
hcsrecho = const(2)   # - distance HCSR04 echo pin
dhtpin = const(20)     # - dht_pin 11 and 22
co2 = const(14)        # - [ADC] CO2
temp6000 = const(13)   # - [ADC] light sensor TEMP6000
ph = const(12)         # - [ADC] PH sensor
ds18 = const(35)       # - DS18B20 - temp. sensor
mic = const(5)         # - [ADC] microphone
