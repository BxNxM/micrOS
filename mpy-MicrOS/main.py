from Network import auto_network_configuration
from SocketServer import server
from LogicalPins import getPlatformValByKey

#################################################################
#               EVENT/INTERRUPT HANDLER INTERFACES              #
#################################################################
def interrupt_handler():
    try:
        from InterruptHandler import enableInterrupt
        enableInterrupt()
    except Exception as e:
        print("DEBUG: InterruptHandler.enableInterrupt error: {}".format(e))

def extrernal_interrupt_handler():
    try:
        from InterruptHandler import init_eventPIN
        init_eventPIN(pin=getPlatformValByKey('button'))
    except Exception as e:
        print("DEBUG: InterruptHandler.init_eventPIN error: {}".format(e))

#################################################################
#                      MAIN FUNCTION CALLS                      #
#################################################################
# NETWORK setup
auto_network_configuration()

# SET interrupt with timirqcbf from nodeconfig
interrupt_handler()

# SET external interrupt with extirqcbf from nodeconfig
extrernal_interrupt_handler()

# RUN Web/Socket server
server.run()
