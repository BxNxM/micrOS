from WiFi import auto_network_configuration
from WebServer import server

def oled_debug_msg(timer=None):
    if timer is not None:
        try:
            # Use from interrupt
            from LM_oled_128x64i2c import show_debug_page
            show_debug_page()
        except:
            print("DEBUG: LM_oled_128x64i2c.wakeup_oled_debug_page_execute error")
    else:
        try:
            # Use if debug mode on
            from LM_oled_128x64i2c import wakeup_oled_debug_page_execute
            wakeup_oled_debug_page_execute()
        except:
            print("DEBUG: LM_oled_128x64i2c.wakeup_oled_debug_page_execute error")

def interrupt_handler():
    try:
        from InterruptHandler import enableInterrupt
        enableInterrupt(cbf=oled_debug_msg, period_ms=6000)
    except:
        print("DEBUG: InterruptHandler.enableInterrupt error")

# Network setup
auto_network_configuration()

# Debug wakeup oled info
oled_debug_msg()

# Enable interrupt with callback function
interrupt_handler()

# Run Web/Socket server
server.run()
