from micropython import const

# ANALOG RGB + WW + CW
redgb = const(25)       # D25 - rgb red channel [PWM CH1]
rgreenb = const(26)     # D26 - rgb green channel [PWM CH2]
rgbue = const(27)       # D27 - rgb blue channel [PWM CH3]

wwhite = const(15)		# D15 - warm white [PWM CH4]
cwhite = const(14)		# D14 - cold white [PWM CH5]

# DIGITAL LED
neop = const(26)       # D26 - WS2812 - neopixel OneWire bus [PWM]


# ACTUATORS
servo_1 = const(14)    # D14 - servo 1 [PWM CH5]
servo_2 = const(4)     # D4 - servo 2 [PWM CH6]

switch_1 = const(18)   # D18 - switch 1 [simple]
switch_2 = const(19)   # D19 - switch 2 [simple]

dim_1 = const(4)       # D4 - dimmer 1 [PWM6]

l298speed = const(5)   # D5 - DC motor pwm control [PWM]
l298dir_1 = const(18)  # D18 - DC motor direction (1)
l298dir_2 = const(19)  # D19 - DC motor direction (2)

l9110dir_1 = const(18) # D18 - DC motor direction (1)
l9110dir_2 = const(19) # D25 - DC motor direction (2)

buzzer = const(33)     # D33 - Buzzer pin - sound generator
haptic = const(32)     # D32 - Haptic - vibration motor


# I2C BUS
i2c_sda = const(21)    # D22 - data
i2c_scl = const(22)    # D21 - clock
trackball_int = const(25)    # D25 - event interrupt


# EXTERNAL EVENT IRQ
irq1 = const(5)         # D5  - event irq pin
irq2 = const(18)        # D18 - event irq pin
irq3 = const(19)        # D19  - event irq pin
irq4 = const(23)        # D23  - event irq pin

js_right = const(23)     # oled_ui joystick
js_left = const(5)
js_up = const(18)
js_down = const(19)
js_press = const(32)    # oled_ui center/ok button

touch_0 = const(32)     # D32 - builtin touch sensor	TODO


# SENSORS
hcsrtrig = const(25)   # D25 - distance HCSR04 trigger pin
hcsrecho = const(26)   # D26 - distance HCSR04 echo pin
dhtpin = const(32)     # D32 - dht_pin 11 and 22
co2 = const(33)        # D33 - CO2 / BATTERY CONFLICT
temp6000 = const(32)   # D32  - light sensor TEMP6000
ph = const(32)         # D32 - PH sensor
ds18 = const(19)       # D19 - DS18B20 - temp. sensor


# TinyPico Built-in
bat_volt = const(35)   # Battery
bat_stat = const(34)   # Battery


"""
# TinyPICO - APA102 Dotstar pins for production boards
DOTSTAR_CLK = const(12)
DOTSTAR_DATA = const(2)
DOTSTAR_PWR = const(13)

# TinyPICO - SPI
SPI_MOSI = const(23)
SPI_CLK = const(18)
SPI_MISO = const(19)

# TinyPICO - DAC
DAC1 = const(25)
DAC2 = const(26)
"""
