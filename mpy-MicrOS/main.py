#################################################################
#                           IMPORTS                             #
#################################################################
try:
    from Network import auto_network_configuration
except Exception as e:
    print("=> [!!!][MAIN DEBUG] Network packacge not available on device: {}".format(e))
    auto_network_configuration = None

from SocketServer import server
from Hooks import bootup_hook, profiling_info

#################################################################
#            INTERRUPT HANDLER INTERFACES / WRAPPERS            #
#################################################################


def interrupt_handler():
    try:
        from InterruptHandler import enableInterrupt
        enableInterrupt()
    except Exception as e:
        print("=> [MAIN DEBUG] InterruptHandler.enableInterrupt error: {}".format(e))


def extrernal_interrupt_handler():
    try:
        from InterruptHandler import init_eventPIN
        init_eventPIN()
    except Exception as e:
        print("=> [MAIN DEBUG] InterruptHandler.init_eventPIN error: {}".format(e))


def safe_boot_hook():
    try:
        bootup_hook()
    except Exception as e:
        print("=> [MAIN DEBUG] Hooks.bootup_hook() error: {}".format(e))

#################################################################
#                      MAIN FUNCTION CALLS                      #
#################################################################


profiling_info(label='[1] MAIN BASELOAD')

# BOOT HOOKs execution
safe_boot_hook()
profiling_info(label='[2] AFTER SAFE BOOT HOOK')

# NETWORK setup
if auto_network_configuration is not None: auto_network_configuration()
profiling_info(label='[3] AFTER NETWORK CONFIGURATION')

# SET interrupt with timirqcbf from nodeconfig
interrupt_handler()
profiling_info(label='[4] AFTER TIMER INTERRUPT SETUP')

# SET external interrupt with extirqcbf from nodeconfig
extrernal_interrupt_handler()
profiling_info(label='[5] AFTER EXTERNAL INTERRUPT SETUP')

# RUN Web/Socket server
server.run()
