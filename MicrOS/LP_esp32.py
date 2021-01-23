from micropython import const

builtin = const(2)    # BUILT IN LED - progress_led
pwm_0 = const(27)     # D27 - servo
pwm_1 = const(14)     # D14 - pwm_red / switch2
pwm_2 = const(12)     # D12 - pwm_green / servo2
pwm_3 = const(15)     # D15 - pwm_blue / neopixel
i2c_sda = const(21)   # D22 - OLED
i2c_scl = const(22)   # D21 - OLED
pwm_4 = const(4)      # D4  - extirqpin
simple_0 = const(26)  # D26 - dist_trigger / switch
pwm_5 = const(33)     # D35 - dist_echo / dimmer
simple_1 = const(32)  # D32 - dht_pin
adc_0 = const(35)     # D33 - CO2
adc_1 = const(36)     # VP  - light sensor TEMP6000
adc_2 = const(39)     # VN  - PH sensor
adc_3 = const(34)     # D34 - water level (barometric)
touch_0 = const(13)   # D13 - touch sensor
