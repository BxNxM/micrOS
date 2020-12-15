"""
Module is responsible for board independent
input/output handling dedicated to micrOS framework.
- Hardware based pinout handling

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                           IMPORTS                             #
#################################################################
from sys import platform

#################################################################
#                        GPI/O ON DEVICE                        #
#################################################################


def get_pin_on_platform_by_key(key):
    if 'esp32' in platform:
        return {'builtin': 2,       # BUILT IN LED - progress_led
                'pwm_0': 27,        # D27 - servo
                'pwm_1': 14,        # D14 - pwm_red / switch2
                'pwm_2': 12,        # D12 - pwm_green / servo2
                'pwm_3': 15,        # D15 - pwm_blue / neopixel
                'i2c_sda': 21,      # D22 - OLED
                'i2c_scl': 22,      # D21 - OLED
                'pwm_4': 4,         # D4  - extirqpin
                'simple_0': 26,     # D26 - dist_trigger / switch
                'pwm_5': 35,        # D35 - dist_echo / dimmer
                'simple_1': 32,     # D32 - dht_pin
                'adc_0': 33,        # D33 - CO2
                'adc_1': 36,        # VP  - light sensor TEMP6000
                'adc_2': 39,        # VN  - PH sensor
                'adc_3': 34,        # D34 - water level (barometric)
                'touch_0': 13,      # D13 - touch sensor
                }.get(key, None)
    if 'esp8266' in platform:
        return {'builtin': 16,    # BUILT IN LED - progress_led
                'pwm_0': 15,      # D8 - servo
                'pwm_1': 13,      # D7 - pwm_red / switch2
                'pwm_2': 2,       # D4 - pwm_green / servo2
                'pwm_3': 0,       # D3 - pwm_blue / neopixel
                'i2c_sda': 4,     # D2 - OLED
                'i2c_scl': 5,     # D1 - OLED
                'pwm_4': 12,      # D6 - extirqpin
                'simple_0': 15,   # D0 - dist_trigger / switch
                'pwm_5': 14,      # D5 - dist_echo / dimmer
                'simple_1': 10,   # SD3 - dht_pin
                'adc_0': 0,       # ADC0 - CO2
                'adc_1': 0,       # ADC0 - light sensor TEMP6000
                'adc_2': 0,       # ADC0 - PH sensor
                'adc_3': 0,       # ADC0 - water lvl
                'simple_2': 9     # SD2 - PIR
                }.get(key, None)
    return None
