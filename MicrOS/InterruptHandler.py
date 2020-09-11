"""
Module is responsible for hardware interrupt
handling dedicated to micrOS framework.
- Setting up interrupt memory buffer from config
- Configure time based and external interrupts

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                            IMPORTS                            #
#################################################################
from ConfigHandler import cfgget, console_write
from InterpreterCore import execute_LM_function_Core
from LogicalPins import get_pin_on_platform_by_key
from Scheduler import scheduler


#################################################################
#            CONFIGURE INTERRUPT MEMORY BUFFER                  #
#################################################################


def set_emergency_buffer():
    irqmembuf = cfgget('irqmembuf')
    emergency_buff_kb = irqmembuf if irqmembuf is not None and isinstance(irqmembuf, int) else 1000
    if cfgget('extirq') or cfgget("timirq"):
        from micropython import alloc_emergency_exception_buf
        console_write("[IRQ] Interrupts was enabled, alloc_emergency_exception_buf={}".format(emergency_buff_kb))
        alloc_emergency_exception_buf(emergency_buff_kb)
    else:
        console_write("[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.")

#################################################################
#                       TIMER INTERRUPT(S)                      #
#################################################################


CFG_TIMIRQCBF = 'n/a'
CFG_CRON_TASKS = 'n/a'


def secureInterruptHandler(timer=None):
    """
    TIMER INTERRUPT CALLBACK FUNCTION WRAPPER
    - FIRST PRIORITY: SCHEDULER
    - SECOND PRIORITY: SIMPLE PERIODIC CALLBACK
    """
    try:
        if CFG_CRON_TASKS.lower() != 'n/a':
            period = int(cfgget("timirqseq"))
            state = scheduler(CFG_CRON_TASKS, period)
            if not state: console_write("[IRQ] TIMIRQ (cron) scheduler error")
            return state
    except Exception as e:
        console_write("[IRQ] TIMIRQ (cron) callback: {} error: {}".format(CFG_CRON_TASKS, e))
        return

    try:
        if CFG_TIMIRQCBF.lower() != 'n/a':
            # Execute CBF from config
            state = execute_LM_function_Core(CFG_TIMIRQCBF.split(' '))
            if not state: console_write("[IRQ] TIMIRQ execute_LM_function_Core error: {}".format(CFG_TIMIRQCBF))
    except Exception as e:
        console_write("[IRQ] TIMIRQ callback: {} error: {}".format(CFG_TIMIRQCBF, e))


def enableInterrupt():
    if cfgget("timirq"):
        # Select simple or advanced scheduler options
        if cfgget('cron'):
            __enableInterruptScheduler()
        else:
            __enableInterruptSimple()


def __enableInterruptSimple():
    """
    SIMPLE TIMER INTERRUPT CONFIGURATION
    """
    global CFG_TIMIRQCBF
    # LOAD DATA FOR TIMER IRQ: cfgget("timirq")
    if cfgget('timirqcbf').lower() != 'n/a':
        CFG_TIMIRQCBF = cfgget('timirqcbf')
        try:
            period_ms_usr = int(cfgget("timirqseq"))
        except Exception as e:
            console_write("[IRQ] TIMIRQ period query error: {}".format(e))
            period_ms_usr = 3000
        console_write("[IRQ] TIMIRQ ENABLED: SEQ: {} CBF: {}".format(period_ms_usr, CFG_TIMIRQCBF))
        from machine import Timer
        # INIT TIMER IRQ with callback function wrapper
        timer = Timer(0)
        timer.init(period=period_ms_usr, mode=Timer.PERIODIC, callback=secureInterruptHandler)
    else:
        console_write("[IRQ] TIMIRQ: isenable: {} callback: {}".format(cfgget("timirq"), cfgget('timirqcbf')))


def __enableInterruptScheduler():
    """
    SMART TIMER INTERRUPT CONFIGURATION
    """
    global CFG_CRON_TASKS
    # LOAD DATA FOR CRON SCHEDULERL: cfgget("timirq") and cfgget('cron')
    if cfgget('cron_tasks') != 'n/a':
        CFG_CRON_TASKS = cfgget('cron_tasks')
        try:
            period_ms_usr = int(cfgget("timirqseq"))
        except Exception as e:
            console_write("[IRQ] TIMIRQ period query error: {}".format(e))
            period_ms_usr = 3000
        console_write("[IRQ] TIMIRQ ENABLED: SEQ: {} TaskScheduler (cron)".format(period_ms_usr))
        from machine import Timer
        # INIT TIMER IRQ with callback function wrapper
        timer = Timer(0)
        timer.init(period=period_ms_usr, mode=Timer.PERIODIC, callback=secureInterruptHandler)
    else:
        console_write("[IRQ] TIMIRQ (cron): isenable: {} tasks: {}".format(cfgget("timirq"), CFG_CRON_TASKS))

#################################################################
#                    EXTERNAL INTERRUPT(S)                      #
#################################################################
# trigger=Pin.IRQ_FALLING   signal HIGH to LOW
# trigger=Pin.IRQ_RISING    signal LOW to HIGH
# trigger=3                 both
#################################################################


CFG_EVIRQCBF = 'n/a'


def secureEventInterruptHandler(pin=None):
    """
    EVENT INTERRUPT CALLBACK FUNCTION WRAPPER
    """
    try:
        if CFG_EVIRQCBF.lower() != 'n/a':
            state = execute_LM_function_Core(CFG_EVIRQCBF.split(' '))
            if not state: console_write("[IRQ] EXTIRQ execute_LM_function_Core error: {}".format(CFG_TIMIRQCBF))
    except Exception as e:
        console_write("[IRQ] EVENTIRQ callback: {} error: {}".format(CFG_EVIRQCBF, e))


def init_eventPIN():
    """
    EVENT INTERRUPT CONFIGURATION
    """
    global CFG_EVIRQCBF
    CFG_EVIRQCBF = cfgget('extirqcbf')
    if cfgget('extirq') and CFG_EVIRQCBF.lower() != 'n/a':
        pin = get_pin_on_platform_by_key('pwm_4')
        console_write("[IRQ] EVENTIRQ ENABLED PIN: {} CBF: {}".format(pin, CFG_EVIRQCBF))
        # Init event irq with callback function wrapper
        from machine import Pin
        pin_obj = Pin(pin, Pin.IN, Pin.PULL_UP)
        pin_obj.irq(trigger=Pin.IRQ_RISING, handler=secureEventInterruptHandler)
    else:
        console_write("[IRQ] EVENTIRQ: isenable: {} callback: {}".format(cfgget('extirq'), CFG_EVIRQCBF))

#################################################################
#                         INIT MODULE                           #
#################################################################


set_emergency_buffer()
