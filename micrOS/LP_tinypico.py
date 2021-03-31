from micropython import const

# ANANLOG RGB
redgb = const(25)       # D25 - rgb red channel [PWM CH1]
rgreenb = const(26)     # D26 - rgb green channel [PWM CH2]
rgbue = const(27)       # D27 - rgb blue channel [PWM CH3]

redgb2 = const(15)      # D15 - rgb2 red channel [PWM CH4]
rgreenb2 = const(14)    # D14 - rgb2 green channel [PWM CH5]
rgbue2 = const(4)       # D4 - rgb2 blue channel [PWM CH6]

wwhite = const(15)		# D15 - warm white [PWM CH4] TODO
cwhite = const(14)		# D14 - cold white [PWM CH5] TODO


# DIGITAL LED
neop = const(23)       # D23 - WS2812 - neopixel OneWire bus [PWM]


# ACTUATORS
servo_1 = const(15)    # D15 - servo 1 [PWM CH4]
servo_2 = const(14)    # D14 - servo 2 [PWM CH5]

switch_1 = const(18)   # D18 - switch 1 [simple]
switch_2 = const(19)   # D19 - switch 2 [simple]

dim_1 = const(4)       # D4 - dimmer 1 [PWM6]

l298speed = const(5)   # D5 - DC motor pwm control [PWM]
l298dir_1 = const(18)  # D18 - DC motor direction (1)
l298dir_2 = const(19)  # D19 - DC motor direction (2)

l9110dir_1 = const(18) # D33 - DC motor direction (1)
l9110dir_2 = const(19) # D25 - DC motor direction (2)

buzzer = const(18)     # D18 - Buzzer pin - sound generator


# I2C BUS
i2c_sda = const(21)    # D22 - data
i2c_scl = const(22)    # D21 - clock


# EXTERNAL EVENT IRQ
extirq = const(5)      # D5  - extirq pin
touch_0 = const(32)    # D32 - builtin touch sensor	TODO


# SENSORS
hcsrtrig = const(25)   # D25 - distance HCSR04 trigger pin
hcsrecho = const(26)   # D26 - distance HCSR04 echo pin
dhtpin = const(32)     # D32 - dht_pin 11 and 22
co2 = const(33)        # D33 - CO2 / BATTERY CONFLICT
temp6000 = const(32)   # D32  - light sensor TEMP6000
ph = const(4)          # D4 - PH sensor
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
