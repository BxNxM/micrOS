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
from Network import auto_nw_config
from Hooks import bootup, profiling_info
from InterruptHandler import enableInterrupt, enableCron
from InterruptHandler import initEventIRQs
from Debug import errlog_add
from Time import ntp_time, suntime


#################################################################
#            INTERRUPT HANDLER INTERFACES / WRAPPERS            #
#################################################################


def safe_boot():
    try:
        bootup()
    except Exception as e:
        print(f"[micrOS main] Hooks.boot() error: {e}")
        errlog_add(f"[ERR] safe_boot: {e}")


def irq_handler():
    try:
        enableInterrupt()
        enableCron()
    except Exception as e:
        print(f"[micrOS main] InterruptHandler.enableInterrupt/CronInterrupt error: {e}")
        errlog_add(f"[ERR] irq_handler error: {e}")


def external_irq_handler():
    try:
        initEventIRQs()
    except Exception as e:
        print(f"[micrOS main] InterruptHandler.initEventIRQs error: {e}")
        errlog_add(f"[ERR] external_irq_handler error: {e}")


#################################################################
#                      MAIN FUNCTION CALLS                      #
#################################################################


def micrOS():
    profiling_info(label='[memUsage] MAIN LOAD')

    # CREATE ASYNC TASK MANAGER
    aio = Manager()

    # BOOT TASKS: Initial LM executions
    safe_boot()

    # SET external interrupt with extirqcbf from nodeconfig
    external_irq_handler()

    # NETWORK setup
    nwmd = auto_nw_config()
    if nwmd == 'STA':
        # Set UTC + SUN TIMES FROM API ENDPOINTS
        suntime()
        # Set NTP - RTC + UTC shift + update uptime (boot time)
        ntp_time()
    else:
        # AP mode - no ntp sync set uptime anyway
        from Time import uptime
        uptime(update=True)

    # SET interrupt with timirqcbf from nodeconfig
    irq_handler()

    # [SocketServer] as async task
    aio.create_task(SocketServer().run_server(), tag='server')
    profiling_info(label='[memUsage] SYSTEM IS UP')

    # [EVENT LOOP] Start async event loop
    aio.run_forever()

    # UNEXPECTED RESTART ???
    errlog_add("[ERR] !!! Unexpected micrOS restart")
