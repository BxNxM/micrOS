from micropython import const

builtin = const(16)    # BUILT IN LED - progress_led
servo_1 = const(15)    # D8 - servo
servo_2 = const(2)     # D4 - servo(2) [PWM]
rgreenb = const(2)     # D4 - rgb green [PWM]
redgb = const(14)      # D7 - rgb red channel [PWM]
switch_1 = const(15)   # D0 - switch(1) [simple]
switch_2 = const(13)   # D7 - switch(2) [simple]
rgbue = const(0)       # D3 - rgb blue channel [PWM]
neop = const(0)        # D3 - neopixel OneWire bus [PWM]
i2c_sda = const(4)     # D2 - oled - data
i2c_scl = const(5)     # D1 - oled - clock
irq1 = const(12)       # D6  - event irq pin
hcsrtrig = const(15)   # D0 - distance HCSR04 trigger pin
hcsrecho = const(14)   # D5 - istance HCSR04 echo pin [PWM]
dim_1 = const(14)      # D5 - dimmer(1) [PWM]
dhtpin = const(10)     # SD3 - dht_pin 11 and 22
co2 = const(0)         # ADC0 - CO2
temp6000 = const(0)    # ADC0 - light sensor TEMP6000
ph = const(0)          # ADC0 - PH sensor
buzzer = const(14)     # D5 - Buzzer pin - sound generator
ds18 = const(9)        # SD2 - DS18B20 - temp. sensor
