from Network import auto_network_configuration
from WebServer import server

#################################################################
#                       CALLBACK FUNCTIONS                      #
#################################################################
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

OLED_INVERT_STATE = False
def external_interrupt_callback(pin=None):
    global OLED_INVERT_STATE
    try:
        from LM_oled_128x64i2c import invert
        from time import sleep
        invert(OLED_INVERT_STATE)
        OLED_INVERT_STATE = not OLED_INVERT_STATE
        sleep(0.3)
    except:
        print("DEBUG: LM_oled_128x64i2c.invert error")


#################################################################
#               EVENT/INTERRUPT HANDLER INTERFACES              #
#################################################################
def interrupt_handler():
    try:
        from InterruptHandler import enableInterrupt
        enableInterrupt(callback=oled_debug_msg, period_ms=5000)
    except:
        print("DEBUG: InterruptHandler.enableInterrupt error")

def extrernal_interrupt_handler():
    try:
        from InterruptHandler import init_eventPIN
        init_eventPIN(callback=external_interrupt_callback, pin=12)
    except:
        print("DEBUG: InterruptHandler.init_eventPIN error")

#################################################################
#                      MAIN FUNCTION CALLS                      #
#################################################################
# NETWORK setup
auto_network_configuration()

# DEBUG wakeup oled info
oled_debug_msg()

# SET interrupt with callback function
interrupt_handler()

# SET external interrupt with callback function
extrernal_interrupt_handler()

# RUN Web/Socket server
server.run()
