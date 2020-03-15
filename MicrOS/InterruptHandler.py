from ConfigHandler import cfgget, console_write
from InterpreterShell import execute_LM_function

#################################################################
#            CONFIGURE INTERRUPT MEMORY BUFFER                  #
#################################################################
def set_emergency_buffer(base_buff_kb=300):
    from micropython import alloc_emergency_exception_buf
    buff_size_kb = 0
    if cfgget("timirq"):
        buff_size_kb += base_buff_kb
    if cfgget('extirq'):
        buff_size_kb += base_buff_kb
    if buff_size_kb > 0:
        console_write("Interrupts was enabled, alloc_emergency_exception_buf={}".format(buff_size_kb))
        alloc_emergency_exception_buf(buff_size_kb)
    else:
        console_write("Interrupts disabled, skip alloc_emergency_exception_buf configuration.")

# Call set_emergency_buffer immediately.
set_emergency_buffer()

#################################################################
#                       TIMER INTERRUPT(S)                      #
#################################################################
TIMIRQ_OVERALP = False
def secureInterruptHandler(timer=None):
    global TIMIRQ_OVERALP
    if not TIMIRQ_OVERALP:
        TIMIRQ_OVERALP = True
        try:
            timirqcbf = cfgget('timirqcbf')
            if timirqcbf != 'n/a':
                execute_LM_function(timirqcbf.split(' '))
        except Exception as e:
            console_write("TIMIRQ callback error: " + str(e))
        TIMIRQ_OVERALP = False
    else:
        console_write("TIMIRQ process overlap... skip job.")

def enableInterrupt(period_ms=4000):
    if cfgget("timirq") and cfgget('timirqcbf') != 'n/a':
        console_write("TIMIRQ ENABLED")
        from machine import Timer
        timer = Timer(0)
        timer.init(period=period_ms, mode=Timer.PERIODIC, callback=secureInterruptHandler)
    else:
        console_write("TIMIRQ: isenable: {} callback: {}".format(cfgget("timirq"), cfgget('timirqcbf')))

#################################################################
#                    EXTERNAL INTERRUPT(S)                      #
#################################################################
# trigger=Pin.IRQ_FALLING   signal HIGH to LOW
# trigger=Pin.IRQ_RISING    signal LOW to HIGH
# trigger=3                 both
#################################################################
EVIRQ_OVERALP = False
def secureEventInterruptHandler(pin=None):
    global EVIRQ_OVERALP
    if not EVIRQ_OVERALP:
        EVIRQ_OVERALP = True
        try:
            extirqcbf = cfgget('extirqcbf')
            if extirqcbf != 'n/a':
                execute_LM_function(extirqcbf.split(' '))
        except Exception as e:
            console_write("EVENTIRQ callback error: " + str(e))
        EVIRQ_OVERALP = False
    else:
        console_write("EVENTIRQ process overlap... skip job.")

def init_eventPIN(pin=12):
    if cfgget('extirq') and cfgget('extirqcbf') != 'n/a':
        console_write("EVENTIRQ ENABLED")
        from machine import Pin
        event_pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        event_pin.irq(trigger=Pin.IRQ_RISING, handler=secureEventInterruptHandler)
    else:
        console_write("EVENTIRQ: isenable: {} callback: {}".format(cfgget('extirq'), cfgget('extirqcbf')))

