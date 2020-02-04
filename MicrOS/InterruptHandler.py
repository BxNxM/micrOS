from ConfigHandler import cfg, console_write

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

def enableInterrupt(cbf=secureInterruptHandler, period_ms=4000):
    global TIMIQQ_CALLBACK
    TIMIQQ_CALLBACK = cbf
    interrupt_is_enabled = cfg.get("timirq")
    if cbf is not None and interrupt_is_enabled:
        from micropython import alloc_emergency_exception_buf
        from machine import Timer
        alloc_emergency_exception_buf(100)
        timer = Timer(0)
        timer.init(period=period_ms, mode=Timer.PERIODIC, callback=secureInterruptHandler)
