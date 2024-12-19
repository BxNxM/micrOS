"""
Module is responsible for high level function invocations
dedicated to micrOS framework.

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                           IMPORTS                             #
#################################################################
from Time import ntp_time, suntime
from Tasks import Manager
from Hooks import bootup, profiling_info
from Network import auto_nw_config
from Server import Server
from Interrupts import enableInterrupt, enableCron, initEventIRQs
from Debug import errlog_add


#################################################################
#            INTERRUPT HANDLER INTERFACES / WRAPPERS            #
#################################################################

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
    try:
        bootup()
    except Exception as e:
        print(f"[micrOS main] Hooks.boot() error: {e}")
        errlog_add(f"[ERR] safe_boot: {e}")

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

    # SET external interrupt with extirqcbf from nodeconfig
    external_irq_handler()
    # SET interrupt with timirqcbf from nodeconfig
    irq_handler()

    # [Server] as async task
    aio.create_task(Server().run_server(), tag='server')
    profiling_info(label='[memUsage] SYSTEM IS UP')

    # [EVENT LOOP] Start async event loop
    aio.run_forever()

    # UNEXPECTED RESTART ???
    errlog_add("[ERR] !!! Unexpected micrOS restart")
