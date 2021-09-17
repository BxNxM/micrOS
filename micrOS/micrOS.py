"""
Module is responsible for high level function invocations
dedicated to micrOS framework.

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                           IMPORTS                             #
#################################################################
from SocketServer import SocketServer
from Network import auto_network_configuration
from Hooks import bootup_hook, profiling_info
from InterruptHandler import enableInterrupt, enableCron
from InterruptHandler import initEventIRQs


#################################################################
#            INTERRUPT HANDLER INTERFACES / WRAPPERS            #
#################################################################


def safe_boot_hook():
    try:
        bootup_hook()
    except Exception as e:
        print("[micrOS main] Hooks.bootup_hook() error: {}".format(e))


def interrupt_handler():
    try:
        enableInterrupt()
        enableCron()
    except Exception as e:
        print("[micrOS main] InterruptHandler.enableInterrupt/CronInterrupt error: {}".format(e))


def external_interrupt_handler():
    try:
        initEventIRQs()
    except Exception as e:
        print("[micrOS main] InterruptHandler.initEventIRQs error: {}".format(e))


#################################################################
#                      MAIN FUNCTION CALLS                      #
#################################################################


def micrOS():
    profiling_info(label='[1] MAIN BASELOAD')

    # BOOT HOOKs execution
    safe_boot_hook()
    profiling_info(label='[2] AFTER SAFE BOOT HOOK')

    # SET external interrupt with extirqcbf from nodeconfig
    external_interrupt_handler()
    profiling_info(label='[3] AFTER EXTERNAL INTERRUPT SETUP')

    # NETWORK setup
    auto_network_configuration()
    profiling_info(label='[4] AFTER NETWORK CONFIGURATION')

    # LOAD Singleton SocketServer [1]
    SocketServer()
    profiling_info(label='[5] AFTER SOCKET SERVER CREATION')

    # SET interrupt with timirqcbf from nodeconfig
    interrupt_handler()
    profiling_info(label='[6] AFTER TIMER INTERRUPT SETUP')

    # RUN Singleton SocketServer - main loop [2]
    SocketServer().run()
