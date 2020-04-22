#################################################################
#                            IMPORTS                            #
#################################################################
from ConfigHandler import cfgget, console_write
from InterpreterCore import execute_LM_function_Core
from LogicalPins import get_pin_on_platform_by_key

#################################################################
#            CONFIGURE INTERRUPT MEMORY BUFFER                  #
#################################################################


def set_emergency_buffer():
    from micropython import alloc_emergency_exception_buf
    irqmembuf = cfgget('irqmembuf')
    emergency_buff_kb = irqmembuf if irqmembuf is not None and isinstance(irqmembuf, int) else 1000
    if cfgget('extirq') or cfgget("timirq"):
        console_write("[IRQ] Interrupts was enabled, alloc_emergency_exception_buf={}".format(emergency_buff_kb))
        alloc_emergency_exception_buf(emergency_buff_kb)
    else:
        console_write("[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.")

#################################################################
#                       TIMER INTERRUPT(S)                      #
#################################################################


CFG_TIMIRQCBF = 'n/a'
def secureInterruptHandler(timer=None):
    """
    TIMER INTERRUPT CALLBACK FUNCTION WRAPPER
    """
    try:
        if CFG_TIMIRQCBF.lower() != 'n/a':
            # Execute CBF from config
            state = execute_LM_function_Core(CFG_TIMIRQCBF.split(' '))
            if not state:
                console_write("[IRQ] TIMIRQ execute_LM_function_Core error: {}".format(CFG_TIMIRQCBF))
    except Exception as e:
        console_write("[IRQ] TIMIRQ callback: {} error: {}".format(CFG_TIMIRQCBF, e))


def enableInterrupt():
    """
    TIMER INTERRUPT CONFIGURATION
    """
    global CFG_TIMIRQCBF
    CFG_TIMIRQCBF = cfgget('timirqcbf')
    if cfgget("timirq") and CFG_TIMIRQCBF.lower() != 'n/a':
        try:
            period_ms_usr = int(cfgget("timirqseq"))
        except Exception as e:
            console_write("[IRQ] TIMIRQ period query error: {}".format(e))
            period_ms_usr = 3000
        console_write("[IRQ] TIMIRQ ENABLED: SEQ: {} CBF: {}".format(period_ms_usr, CFG_TIMIRQCBF))
        from machine import Timer
        timer = Timer(0)
        timer.init(period=period_ms_usr, mode=Timer.PERIODIC, callback=secureInterruptHandler)
    else:
        console_write("[IRQ] TIMIRQ: isenable: {} callback: {}".format(cfgget("timirq"), cfgget('timirqcbf')))

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
            if not state:
                console_write("[IRQ] EXTIRQ execute_LM_function_Core error: {}".format(CFG_TIMIRQCBF))
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
        from machine import Pin
        event_pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        event_pin.irq(trigger=Pin.IRQ_RISING, handler=secureEventInterruptHandler)
    else:
        console_write("[IRQ] EVENTIRQ: isenable: {} callback: {}".format(cfgget('extirq'), CFG_EVIRQCBF))

#################################################################
#                         INIT MODULE                           #
#################################################################


set_emergency_buffer()

