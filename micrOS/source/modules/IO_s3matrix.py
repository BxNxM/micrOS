from micropython import const

# ESP32-S3 Matrix 8x8 RGB-LED WiFi Bluetooth With QST Attitude Gyro Sensor QMI8658C
# https://spotpear.com/shop/ESP32-S3FH4R2-Matrix-8x8-RGB-LED-WiFi-Bluetooth-QST-Attitude-Gyro-Sensor-QMI8658C-Arduino-Python-ESP-IDF.html

# Progress LED (no builting available)
builtin = const(1)     # LED - progress_led

# DIGITAL LED
neop = const(14)       # - neopixel OneWire bus [PWM]

# I2C BUS (QMI8658C GYRO)
i2c_sda = const(11)    # - data
i2c_scl = const(12)    # - clock


# EXTERNAL EVENT IRQ
irq1 = const(33)        # - event irq pin
irq2 = const(34)        # - event irq pin
irq3 = const(35)        # - event irq pin
irq4 = const(36)        # - event irq pin
