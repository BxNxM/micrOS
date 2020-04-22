#################################################################
#                           IMPORTS                             #
#################################################################
from sys import platform

#################################################################
#                        GPI/O ON DEVICE                        #
#################################################################


def get_pin_on_platform_by_key(key):
    function_pins_on_platfrom_dict = {}
    if 'esp32' in platform:
        function_pins_on_platfrom_dict = {'builtin': 2}     # BUILT IN LED - progress_led
    elif 'esp8266' in platform:
        function_pins_on_platfrom_dict = {'builtin': 16,    # BUILT IN LED - progress_led
                                          'pwm_0': 15,      # D8 - servo
                                          'pwm_1': 13,      # D7 - pwm_red
                                          'pwm_2': 2,       # D4 - pwm_green / servo2
                                          'pwm_3': 0,       # D3 - pwm_blue / neopixel
                                          'i2c_sda': 4,     # D2 - OLED
                                          'i2c_scl': 5,     # D1 - OLED
                                          'pwm_4': 12,      # D6 - extirqpin
                                          'simple_0': 16,   # D0 - dist_trigger
                                          'pwm_5': 14,      # D5 - dist_echo
                                          'simple_1': 10,   # SD3 - dht_pin
                                          'adc_0': 0,       # ADC0 - CO2
                                          'simple_2': 9     # SD2 - PIR
                                          }
    return function_pins_on_platfrom_dict.get(key, None)
