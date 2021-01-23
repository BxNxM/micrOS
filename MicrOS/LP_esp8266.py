from micropython import const

builtin = const(16)    # BUILT IN LED - progress_led
pwm_0 = const(15)      # D8 - servo
pwm_1 = const(13)      # D7 - pwm_red / switch2
pwm_2 = const(2)       # D4 - pwm_green / servo2
pwm_3 = const(0)       # D3 - pwm_blue / neopixel
i2c_sda = const(4)     # D2 - OLED
i2c_scl = const(5)     # D1 - OLED
pwm_4 = const(12)      # D6 - extirqpin
simple_0 = const(15)   # D0 - dist_trigger / switch
pwm_5 = const(14)      # D5 - dist_echo / dimmer
simple_1 = const(10)   # SD3 - dht_pin
adc_0 = const(0)       # ADC0 - CO2
adc_1 = const(0)       # ADC0 - light sensor TEMP6000
adc_2 = const(0)       # ADC0 - PH sensor
adc_3 = const(0)       # ADC0 - water lvl
simple_2 = const(9)    # SD2 - PIR
