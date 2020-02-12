from sys import platform

def getPlatformValByKey(key):
    function_pins_on_platfrom_dict = {}
    if 'esp32' in platform:
        function_pins_on_platfrom_dict = {'progressled': 2}
    elif 'esp8266' in platform:
        function_pins_on_platfrom_dict = {'progressled': 16}
    return function_pins_on_platfrom_dict.get(key, None)
