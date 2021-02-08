"""
Module is responsible for hardware interrupt
handling dedicated to micrOS framework.
- Setting up interrupt memory buffer from config
- Configure time based and external interrupts

- Time based IRQ:
    - Simple (timer0) with fix period callback
    - Advanced (timer1) - time stump ! LM function;
            0-6:0-24:0-59:0-59!system heartbeat; etc.

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                            IMPORTS                            #
#################################################################
from ConfigHandler import cfgget, console_write
from InterpreterCore import execute_LM_function_Core
from LogicalPins import get_pin_on_platform_by_key
if cfgget('cron'):
    # Only import when enabled - memory usage optimization
    from Scheduler import scheduler

#################################################################
#            CONFIGURE INTERRUPT MEMORY BUFFER                  #
#################################################################


def emergency_mbuff():
    emergency_buff_kb = cfgget('irqmembuf')
    if cfgget('extirq') or cfgget("timirq"):
        from micropython import alloc_emergency_exception_buf
        console_write("[IRQ] Interrupts was enabled, alloc_emergency_exception_buf={}".format(emergency_buff_kb))
        alloc_emergency_exception_buf(emergency_buff_kb)
    else:
        console_write("[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.")

#################################################################
#                       TIMER INTERRUPT(S)                      #
#################################################################

#############################################
#    [TIMER 0] TIMIRQ CBFs - LM executor    #
#############################################


def timirq_cbfs(tasks):
    """
    LM tasks executor callback function
    """
    try:
        # Execute CBF from cached config
        for cmd in (cmd.strip().split(' ') for cmd in tasks.split(';')):
            state = execute_LM_function_Core(cmd)
            if not state:
                console_write("[IRQ] TIMIRQ execute_LM_function_Core error: {}".format(tasks))
    except Exception as e:
        console_write("[IRQ] TIMIRQ callback: {} error: {}".format(tasks, e))


def enableInterrupt():
    """
    Set task pool executor in interrupt timer0
    Input: timirq(bool), timirqseq(ms), timirqcbf(str)
    """
    console_write("[IRQ] TIMIRQ SETUP: {} SEQ: {}".format(cfgget("timirq"), cfgget("timirqseq")))
    console_write("|- [IRQ] TIMIRQ CBF:{}".format(cfgget('timirqcbf')))
    if cfgget("timirq") and cfgget('timirqcbf').lower() != 'n/a':
        from machine import Timer
        # INIT TIMER IRQ with callback function wrapper
        timer = Timer(0)
        timer.init(period=int(cfgget("timirqseq")), mode=Timer.PERIODIC,
                   callback=lambda timer: timirq_cbfs(cfgget('timirqcbf')))


#############################################
#    [TIMER 1] TIMIRQ CRON - LM executor    #
#############################################

def timirq_cbf_sched(task, seq):
    try:
        # Execute CBF LIST from local cached config with timirqseq in sec
        scheduler(task, seq)
    except Exception as e:
        console_write("[IRQ] TIMIRQ (cron) callback: {} error: {}".format(task, e))


def enableCron():
    """
    Set time stump based scheduler aka cron in timer1
    Input: cron(bool), cronseq(ms), crontasks(str)
    """
    console_write("[IRQ] CRON IRQ SETUP: {} SEQ: {}".format(cfgget(cfgget('cron')), cfgget("cronseq")))
    console_write("|- [IRQ] CRON CBF:{}".format(cfgget('crontasks')))
    if cfgget("cron") and cfgget('crontasks').lower() != 'n/a':
        from machine import Timer
        # INIT TIMER 1 IRQ with callback function wrapper
        timer = Timer(1)
        timer.init(period=int(cfgget("cronseq")), mode=Timer.PERIODIC,
                   callback=lambda timer: timirq_cbf_sched(cfgget('crontasks'), int(cfgget("cronseq")/1000)))


#################################################################
#                  EVENT/EXTERNAL INTERRUPT(S)                  #
#################################################################
# trigger=Pin.IRQ_FALLING   signal HIGH to LOW
# trigger=Pin.IRQ_RISING    signal LOW to HIGH
#################################################################


def extirq_cbf(task):
    """
    EVENT INTERRUPT CALLBACK FUNCTION WRAPPER
    """
    try:
        state = execute_LM_function_Core(task.split(' '))
        if not state:
            console_write("[IRQ] EXTIRQ execute_LM_function_Core error: {}".format(task))
    except Exception as e:
        console_write("[IRQ] EVENTIRQ callback: {} error: {}".format(task, e))


def init_eventPIN():
    """
    EVENT INTERRUPT CONFIGURATION
    """
    console_write("[IRQ] EXTIRQ SETUP - EXTIRQ: {} TRIG: {}".format(cfgget("extirq"), cfgget("extirqtrig")))
    console_write("|- [IRQ] EXTIRQ CBF: {}".format(cfgget('extirqcbf')))
    if cfgget('extirq') and cfgget('extirqcbf').lower() != 'n/a':
        pin = get_pin_on_platform_by_key('pwm_4')
        trig = cfgget('extirqtrig').strip().lower()
        # Init event irq with callback function wrapper
        from machine import Pin
        pin_obj = Pin(pin, Pin.IN, Pin.PULL_UP)
        console_write("[IRQ] - event setup: {}".format(trig))
        if trig == 'down':
            pin_obj.irq(trigger=Pin.IRQ_FALLING, handler=extirq_cbf)
            return
        if trig == 'both':
            pin_obj.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=extirq_cbf)
            return
        pin_obj.irq(trigger=Pin.IRQ_RISING, handler=lambda pin: extirq_cbf(cfgget('extirqcbf')))


#################################################################
#                         INIT MODULE                           #
#################################################################


emergency_mbuff()
