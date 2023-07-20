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

Reference: https://docs.micropython.org/en/latest/library/machine.Pin.html
"""
#################################################################
#                            IMPORTS                            #
#################################################################
from machine import Pin
from utime import ticks_ms, ticks_diff
from ConfigHandler import cfgget
from Debug import console_write, errlog_add
from TaskManager import exec_lm_pipe_schedule
from LogicalPins import physical_pin
if cfgget('cron'):
    # Only import when enabled - memory usage optimization
    from Scheduler import scheduler

#################################################################
#            CONFIGURE INTERRUPT MEMORY BUFFER                  #
#################################################################


def emergency_mbuff():
    emergency_buff_kb = 1000
    if cfgget('cron') or cfgget('extirq') or cfgget("timirq"):
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


def enableInterrupt():
    """
    Set task pool executor in interrupt timer0
    Input: timirq(bool), timirqseq(ms), timirqcbf(str)
    """
    console_write("[IRQ] TIMIRQ SETUP: {} SEQ: {}".format(cfgget("timirq"), cfgget("timirqseq")))
    console_write("|- [IRQ] TIMIRQ CBF:{}".format(cfgget('timirqcbf')))
    if cfgget("timirq"):
        from machine import Timer
        # INIT TIMER IRQ with callback function wrapper
        lm_str = cfgget('timirqcbf')
        timer = Timer(0)
        timer.init(period=int(cfgget("timirqseq")), mode=Timer.PERIODIC,
                   callback=lambda timer: exec_lm_pipe_schedule(lm_str))


#############################################
#    [TIMER 1] TIMIRQ CRON - LM executor    #
#############################################

def enableCron():
    """
    Set time stump based scheduler aka cron in timer1
    Input: cron(bool), crontasks(str)
    """
    timer_period = 3000         # Timer period ms
    console_write("[IRQ] CRON IRQ SETUP: {} SEQ: {}".format(cfgget('cron'), timer_period))
    console_write("|- [IRQ] CRON CBF:{}".format(cfgget('crontasks')))
    if cfgget("cron") and cfgget('crontasks').lower() != 'n/a':
        from machine import Timer
        # INIT TIMER 1 IRQ with callback function wrapper
        lm_str = cfgget('crontasks')
        sample = int(timer_period/1000)
        timer = Timer(1)
        timer.init(period=timer_period, mode=Timer.PERIODIC,
                   callback=lambda timer: scheduler(lm_str, sample))


#################################################################
#                  EVENT/EXTERNAL INTERRUPT(S)                  #
#################################################################
# trigger=Pin.IRQ_FALLING   signal HIGH to LOW
# trigger=Pin.IRQ_RISING    signal LOW to HIGH
#################################################################

def initEventIRQs():
    """
    EVENT INTERRUPT CONFIGURATION - multiple
    """
    # prell_last = {'Pin(1)': 'pin last call time', 'Pin(2)': 'pin last call time', ...}
    prell_last = {}
    prell_ms = cfgget("irq_prell_ms")

    def __edge_exec(_pin_obj, _p_last, _cbf):
        """
        Prell filter / edge detection and execution
        :param _pin_obj: pin obj name
        :param resolver: callback resolver dict,  LM_cbf obj by pins {PinKey: [LM_cbf, prellTimer]}
        :return: None
        """
        nonlocal prell_ms
        _pin = str(_pin_obj)
        # Get stored tick by pin - last successful trigger
        last = _p_last.get(_pin)
        # Calculate trigger diff in ms (from now)
        diff = ticks_diff(ticks_ms(), last)
        # console_write(f"[IRQ] Event {_pin} - tick diff: {diff}")
        # Threshold between ext. irq evens
        if abs(diff) > prell_ms:
            # Save now tick - last trigger action
            _p_last[_pin] = ticks_ms()
            # [!] Execute User Load module by pin number (with micropython.schedule wrapper)
            # console_write(f"---> action")
            exec_lm_pipe_schedule(_cbf)

    def __core(_pin, _trig, _lm_cbf):
        """Run External/Event IRQ setup with __edge_exec callback handler"""
        nonlocal prell_last
        if _pin:
            # [*] update resolver dict by pin number (available in irq callback):
            # PinKey: [CallbackFunction, PrellTimer]  (prell: contact recurrence - fake event filtering... :D)
            prell_last['Pin({})'.format(_pin)] = 0
            _trig = _trig.strip().lower()
            # Init event irq with callback function wrapper
            # pin_obj = Pin(pin, Pin.IN, Pin.PULL_UP) ?TODO?: expose built in resistor parameter ?
            _pin_obj = Pin(_pin, Pin.IN, Pin.PULL_DOWN)
            # [IRQ] - event type setup
            if _trig == 'down':
                _pin_obj.irq(trigger=Pin.IRQ_FALLING,
                             handler=lambda pin: __edge_exec(pin, prell_last, _lm_cbf))
                return
            if _trig == 'both':
                _pin_obj.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
                             handler=lambda pin: __edge_exec(pin, prell_last, _lm_cbf))
                return
            # Default - 'up'
            _pin_obj.irq(trigger=Pin.IRQ_RISING,
                         handler=lambda pin: __edge_exec(pin, prell_last, _lm_cbf))
            return
        console_write("|-- [IRQ] invalid pin: {}".format(_pin))

    def __get_pin(_p):
        """
        Resolve pin by name
        """
        try:
            return physical_pin(_p)
        except Exception as e:
            msg = f'[ERR] EVENT {_p} IO error: {e}'
            console_write("|-- [!] {}".format(msg))
            errlog_add(msg)
        return None

    # Load External IRQ (1-4) execution data set from node config
    for i in range(1, 5):
        # load IRQx params
        irq_en = cfgget(f"irq{i}")
        irq_cbf = cfgget(f"irq{i}_cbf")
        irq_trig = cfgget(f"irq{i}_trig")
        console_write("[IRQ] EXTIRQ SETUP - EXT IRQ{}: {} TRIG: {}".format(i, irq_en, irq_trig))
        console_write("|- [IRQ] EXTIRQ CBF: {}".format(irq_cbf))
        # Init external IRQx
        if irq_en and irq_cbf.strip() != "n/a":
            __core(_pin=__get_pin(f"irq{i}"), _trig=irq_trig, _lm_cbf=irq_cbf)

#################################################################
#                         INIT MODULE                           #
#################################################################


emergency_mbuff()
