from ConfigHandler import cfg, console_write

def handleInterrupt(timer=None):
    console_write("HeartBeat...")

def enableInterrupt(cbf=handleInterrupt, period_ms=4000):
    interrupt_is_enabled = cfg.get("timirq")
    if cbf is not None and interrupt_is_enabled:
        from micropython import alloc_emergency_exception_buf
        from machine import Timer
        alloc_emergency_exception_buf(10)
        timer = Timer(0)
        timer.init(period=period_ms, mode=Timer.PERIODIC, callback=cbf)
