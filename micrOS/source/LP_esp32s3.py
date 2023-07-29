from micropython import const

# BUILTIN LED
builtin = const(38)     # BUILT IN LED - progress_led

###########################
# TODO: review pins below #
###########################

# ANALOG RGB + WW + CW
redgb = const(18)      # - rgb red channel [PWM]
rgreenb = const(17)    # - rgb green channel [PWM]
rgbue = const(16)      # - rgb blue channel [PWM]

wwhite = const(15)	   # - warm white [PWM]
cwhite = const(14)	   # - cold white [PWM]


# DIGITAL LED
neop = const(6)       # - neopixel OneWire bus [PWM]


# ACTUATORS
servo_1 = const(13)    # - servo(1) [PWM]
servo_2 = const(12)    # - servo(2) [PWM]

switch_1 = const(11)   # - switch(1) [simple]
switch_2 = const(10)   # - switch(2) [simple]
switch_3 = const(9)    # - switch(3) [simple]
switch_4 = const(8)    # - switch(4) [simple]

dim_1 = const(7)      # - dimmer(1) [PWM]

l298speed = const(46)  # - DC motor pwm control [PWM]
l298dir_1 = const(45)  # - DC motor direction (1)
l298dir_2 = const(44)  # - DC motor direction (2)

l9110dir_1 = const(37) # - DC motor direction (1)
l9110dir_2 = const(36) # - DC motor direction (2)

buzzer = const(43)     # - Buzzer pin - sound generator


stppr_1 = const(35)    # - stepper motor pin
stppr_2 = const(34)    # - stepper motor pin
stppr_3 = const(33)    # - stepper motor pin
stppr_4 = const(26)    # - stepper motor pin


# I2C BUS
i2c_sda = const(48)    # - oled - data
i2c_scl = const(47)    # - oled - clock


# EXTERNAL EVENT IRQ
irq1 = const(0)        # - event irq pin
irq2 = const(1)        # - event irq pin
irq3 = const(2)        # - event irq pin
irq4 = const(3)        # - event irq pin
oleduibttn = const(4)  # - oled_ui center/ok button

touch_0 = const(5)     # - touch sensor TODO


# SENSORS
hcsrtrig = const(42)   # - distance HCSR04 trigger pin
hcsrecho = const(41)   # - distance HCSR04 echo pin
dhtpin = const(46)     # - dht_pin 11 and 22
co2 = const(45)        # - [ADC] CO2
temp6000 = const(44)   # - [ADC] light sensor TEMP6000
ph = const(37)         # - [ADC] PH sensor
ds18 = const(36)       # - DS18B20 - temp. sensor
mic = const(5)         # - [ADC] microphone
