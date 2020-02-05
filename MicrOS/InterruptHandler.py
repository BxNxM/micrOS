from ConfigHandler import cfgget, console_write
from micropython import alloc_emergency_exception_buf
alloc_emergency_exception_buf(100)

#################################################################
#                       TIMER INTERRUPT(S)                      #
#################################################################
TIMIRQ_OVERALP = False
TIMIQQ_CALLBACK = None
def secureInterruptHandler(timer=None):
    global TIMIRQ_OVERALP, TIMIQQ_CALLBACK
    if not TIMIRQ_OVERALP and TIMIQQ_CALLBACK is not None:
        TIMIRQ_OVERALP = True
        try:
            TIMIQQ_CALLBACK(timer)
        except Exception as e:
            console_write("TIMIRQ callback error: " + str(e))
        TIMIRQ_OVERALP = False
    else:
        console_write("TIMIRQ process overlap... skip job.")

def enableInterrupt(callback=None, period_ms=4000):
    global TIMIQQ_CALLBACK
    TIMIQQ_CALLBACK = callback
    interrupt_is_enabled = cfgget("timirq")
    if callback is not None and interrupt_is_enabled:
        console_write("TIMIRQ ENABLED")
        from machine import Timer
        timer = Timer(0)
        timer.init(period=period_ms, mode=Timer.PERIODIC, callback=secureInterruptHandler)
    else:
        console_write("TIMIRQ: isenable: {} callback: {}".format(interrupt_is_enabled, callback))

#################################################################
#                    EXTERNAL INTERRUPT(S)                      #
#################################################################
EVIRQ_OVERALP = False
EVIQQ_CALLBACK = None
def secureEventInterruptHandler(pin=None):
    global EVIRQ_OVERALP, EVIQQ_CALLBACK
    if not EVIRQ_OVERALP and EVIQQ_CALLBACK is not None:
        EVIRQ_OVERALP = True
        try:
            EVIQQ_CALLBACK(pin)
        except Exception as e:
            console_write("EVENTIRQ callback error: " + str(e))
        EVIRQ_OVERALP = False
    else:
        console_write("EVENTIRQ process overlap... skip job.")

def init_eventPIN(callback=None, pin=12):
    global EVIQQ_CALLBACK
    EVIQQ_CALLBACK = callback
    interrupt_is_enabled = cfgget('extirq')
    if callback is not None and interrupt_is_enabled:
        console_write("EVENTIRQ ENABLED")
        from machine import Pin
        event_pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        event_pin.irq(trigger=Pin.IRQ_FALLING, handler=secureEventInterruptHandler)
    else:
        console_write("EVENTIRQ: isenable: {} callback: {}".format(interrupt_is_enabled, callback))

