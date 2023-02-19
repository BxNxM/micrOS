"""
Module is responsible for high level function invocations
dedicated to micrOS framework.

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                           IMPORTS                             #
#################################################################
from TaskManager import Manager
from SocketServer import SocketServer
from Network import auto_network_configuration
from Hooks import bootup_hook, profiling_info
from InterruptHandler import enableInterrupt, enableCron
from InterruptHandler import initEventIRQs
from Debug import errlog_add
from Time import ntptime, suntime


#################################################################
#            INTERRUPT HANDLER INTERFACES / WRAPPERS            #
#################################################################


def safe_boot_hook():
    try:
        bootup_hook()
    except Exception as e:
        print("[micrOS main] Hooks.bootup_hook() error: {}".format(e))
        errlog_add("[ERR] safe_boot_hook error: {}".format(e))


def interrupt_handler():
    try:
        enableInterrupt()
        enableCron()
    except Exception as e:
        print("[micrOS main] InterruptHandler.enableInterrupt/CronInterrupt error: {}".format(e))
        errlog_add("[ERR] interrupt_handler error: {}".format(e))


def external_interrupt_handler():
    try:
        initEventIRQs()
    except Exception as e:
        print("[micrOS main] InterruptHandler.initEventIRQs error: {}".format(e))
        errlog_add("[ERR] external_interrupt_handler error: {}".format(e))


def nw_time_sync():
    # Set UTC + SUN TIMES FROM API ENDPOINTS
    suntime()
    # Set NTP - RTC + UTC shift
    ntptime()


#################################################################
#                      MAIN FUNCTION CALLS                      #
#################################################################


def micrOS():
    profiling_info(label='[memUsage] MAIN LOAD')

    # CREATE ASYNC TASK MANAGER
    aio_man = Manager()

    # BOOT HOOK: Initial LM executions
    safe_boot_hook()

    # SET external interrupt with extirqcbf from nodeconfig
    external_interrupt_handler()

    # NETWORK setup
    nwmd = auto_network_configuration()
    if nwmd == 'STA':
        nw_time_sync()

    # SET interrupt with timirqcbf from nodeconfig
    interrupt_handler()
    profiling_info(label='[memUsage] SYSTEM IS UP')

    # [SocketServer] as async task
    aio_man.create_task(SocketServer().run_server(), tag='server')
    # [EVENT LOOP] Start async event loop
    aio_man.run_forever()

    # UNEXPECTED RESTART ???
    errlog_add("[ERR] !!! Unexpected micrOS restart")
