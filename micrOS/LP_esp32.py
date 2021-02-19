from micropython import const

builtin = const(2)     # BUILT IN LED - progress_led
servo_1 = const(27)    # D27 - servo(1) [PWM]
servo_2 = const(12)    # D12 - servo(2) [PWM]
rgreenb = const(12)    # D12 - rgb green channel [PWM]
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
co2 = const(35)        # D35 - CO2
temp6000 = const(36)   # VP - light sensor TEMP6000
ph = const(39)         # VN - PH sensor
touch_0 = const(13)    # D13 - touch sensor
