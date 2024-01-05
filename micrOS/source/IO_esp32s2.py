from micropython import const

# BUILTIN LED
builtin = const(15)      # BUILT IN LED - progress_led

# ANALOG RGB + WW + CW
redgb = const(7)        # rgb red channel [PWM]
rgreenb = const(5)      # rgb green channel [PWM]
rgbue = const(3)        # rgb blue channel [PWM]

wwhite = const(12)	    # warm white [PWM]
cwhite = const(11)	    # cold white [PWM]


# DIGITAL LED
neop = const(18)        # neopixel OneWire bus [PWM]


# ACTUATORS
servo_1 = const(12)     # servo(1) [PWM]
servo_2 = const(11)     # servo(2) [PWM]

switch_1 = const(40)    # switch(1) [simple]
switch_2 = const(38)    # switch(2) [simple]
switch_3 = const(36)    # switch(3) [simple]
switch_4 = const(34)    # switch(4) [simple]

dim_1 = const(16)       # dimmer(1) [PWM]

l298speed = const(6)    # DC motor pwm control [PWM]
l298dir_1 = const(4)    # DC motor direction (1)
l298dir_2 = const(2)    # DC motor direction (2)

l9110dir_1 = const(6)   # DC motor direction (1)
l9110dir_2 = const(4)   # DC motor direction (2)

buzzer = const(10)      # Buzzer pin - sound generator

stppr_1 = const(1)      # stepper motor pin
stppr_2 = const(2)      # stepper motor pin
stppr_3 = const(4)      # stepper motor pin
stppr_4 = const(6)      # stepper motor pin


# I2C BUS
i2c_sda = const(18)       # oled - data
i2c_scl = const(16)       # oled - clock


# EXTERNAL EVENT IRQ
irq1 = const(39)         # event irq pin
irq2 = const(37)         # event irq pin
irq3 = const(35)         # event irq pin
irq4 = const(33)         # event irq pin
oleduibttn = const(34)   # oled_ui center/ok button


# SENSORS
hcsrtrig = const(34)    # distance HCSR04 trigger pin
hcsrecho = const(36)    # distance HCSR04 echo pin
dhtpin = const(17)      # dht_pin 11 and 22
co2 = const(13)         # [ADC] CO2
temp6000 = const(10)    # [ADC] light sensor TEMP6000
ph = const(1)           # [ADC] PH sensor
ds18 = const(21)        # DS18B20 - temp. sensor
mic = const(14)         # [ADC] microphone
rot_dt = const(33)      # [IRQ] rotary encoder data
rot_clk = const(35)     # [IRQ] rotary encoder clock
