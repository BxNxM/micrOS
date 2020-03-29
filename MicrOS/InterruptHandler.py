from ConfigHandler import cfgget, console_write
from InterpreterShell import execute_LM_function_Core
from LogicalPins import getPlatformValByKey

#################################################################
#            CONFIGURE INTERRUPT MEMORY BUFFER                  #
#################################################################


def set_emergency_buffer(base_buff_kb=200):
    from micropython import alloc_emergency_exception_buf
    buff_size_kb = 0
    print("=+=> [DEBUG] set_emergency_buffer")
    if cfgget("timirq"):
        buff_size_kb += base_buff_kb
    if cfgget('extirq'):
        buff_size_kb += int(base_buff_kb / 2)
    if buff_size_kb > 0:
        console_write("[IRQ] Interrupts was enabled, alloc_emergency_exception_buf={}".format(buff_size_kb))
        alloc_emergency_exception_buf(buff_size_kb)
    else:
        console_write("Interrupts disabled, skip alloc_emergency_exception_buf configuration.")

#################################################################
#                       TIMER INTERRUPT(S)                      #
#################################################################


CFG_TIMIRQCBF = 'n/a'
def secureInterruptHandler(timer=None):
    try:
        if CFG_TIMIRQCBF.lower() != 'n/a':
            state = execute_LM_function_Core(CFG_TIMIRQCBF.split(' '))
            if not state:
                console_write("[IRQ] {} execute_LM_function_Core error: {}".format(CFG_TIMIRQCBF))
    except Exception as e:
        console_write("[IRQ] TIMIRQ callback: {} error: " + str(e, CFG_TIMIRQCBF))


def enableInterrupt(period_ms=3000):
    global CFG_TIMIRQCBF
    CFG_TIMIRQCBF = cfgget('timirqcbf')
    if cfgget("timirq") and CFG_TIMIRQCBF.lower() != 'n/a':
        try:
            period_ms_usr = int(cfgget("timirqseq"))
        except Exception as e:
            console_write("[IRQ] TIMIRQ period query error: {}".format(e))
            period_ms_usr = period_ms
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
def secureEventInterruptHandler():
    try:
        if CFG_EVIRQCBF.lower() != 'n/a':
            execute_LM_function_Core(CFG_EVIRQCBF.split(' '))
    except Exception as e:
        console_write("[IRQ] EVENTIRQ callback: {} error: " + str(CFG_EVIRQCBF, e))



def init_eventPIN():
    global CFG_EVIRQCBF
    CFG_EVIRQCBF = cfgget('extirqcbf')
    if cfgget('extirq') and CFG_EVIRQCBF.lower() != 'n/a':
        pin = getPlatformValByKey('extirqpin')
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

