from sys import platform

def getPlatformValByKey(key):
    function_pins_on_platfrom_dict = {}
    if 'esp32' in platform:
        function_pins_on_platfrom_dict = {'progressled': 2}
    elif 'esp8266' in platform:
        function_pins_on_platfrom_dict = {'progressled': 16,    # BUILT IN LED
                                          'servo': 15,          # D8
                                          'pwm_red': 2,         # D4
                                          'pwm_green': 13,      # D7
                                          'pwm_blue': 0,        # D3
                                          'i2c_sda': 4,         # D2
                                          'i2c_scl': 5,         # D1
                                          'extirqpin': 12,      # D6
                                          'dist_trigger': 16,   # D0
                                          'dist_echo': 14       # D5
                                          }
    return function_pins_on_platfrom_dict.get(key, None)
