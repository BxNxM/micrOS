from WiFi import auto_network_configuration
from WebServer import server
import WebServer

def oled_debug_msg():
    try:
        from LM_oled_128x64i2c import wakeup_oled_debug_page_execute
        wakeup_oled_debug_page_execute()
    except:
        print("DEBUG: LM_oled_128x64i2c.wakeup_oled_debug_page_execute.")

auto_network_configuration()
oled_debug_msg()
server.run()
