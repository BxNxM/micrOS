from Network import auto_network_configuration
from SocketServer import server
from sys import modules

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
        init_eventPIN()
    except Exception as e:
        print("DEBUG: InterruptHandler.init_eventPIN error: {}".format(e))

def cleanup_modules():
    del modules['Network']

#################################################################
#                      MAIN FUNCTION CALLS                      #
#################################################################
# NETWORK setup
auto_network_configuration()

# SET interrupt with timirqcbf from nodeconfig
interrupt_handler()

# SET external interrupt with extirqcbf from nodeconfig
extrernal_interrupt_handler()

# Clean up unused modules
cleanup_modules()

# RUN Web/Socket server
server.run()
