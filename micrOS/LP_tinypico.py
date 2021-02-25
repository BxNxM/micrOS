from micropython import const

servo_1 = const(27)    # D27 - servo(1) [PWM]
servo_2 = const(18)    # D18 - (SPI-SCK) servo(2) [PWM]
rgreenb = const(18)    # D18 - (SPI-SCK) rgb green channel [PWM]
redgb = const(14)      # D14 - rgb red channel [PWM]
switch_1 = const(26)   # D26 - switch(1) [simple]
switch_2 = const(14)   # D14 - switch(2) [simple]
rgbue = const(15)      # D15 - rgb blue channel [PWM]
neop = const(15)       # D15 - neopixel OneWire bus [PWM]
i2c_sda = const(21)    # D22 - oled - data
i2c_scl = const(22)    # D21 - oled - clock
extirq = const(4)      # D4  - extirq pin
hcsrtrig = const(26)   # D26 - distance HCSR04 trigger pin
hcsrecho = const(33)   # D33 - distance HCSR04 echo pin
dim_1 = const(33)      # D33 - dimmer(1) [PWM]
l298speed = const(32)  # D32 - DC motor pwm control [PWM]
l298dir_1 = const(33)  # D33 - DC motor direction (1)
l298dir_2 = const(25)  # D25 - DC motor direction (2)
dhtpin = const(32)     # D32 - dht_pin 11 and 22
co2 = const(35)        # D35 - CO2 / BATTERY CONFLICT
temp6000 = const(5)    # D5  - (SPI-SS) light sensor TEMP6000
ph = const(19)         # D19 - (SPI-MISO) PH sensor
touch_0 = const(33)    # D33 - touch sensor
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
