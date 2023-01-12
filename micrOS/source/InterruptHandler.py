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
from utime import ticks_us, ticks_diff
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
    Input: cron(bool), cronseq(ms), crontasks(str)
    """
    console_write("[IRQ] CRON IRQ SETUP: {} SEQ: {}".format(cfgget('cron'), cfgget("cronseq")))
    console_write("|- [IRQ] CRON CBF:{}".format(cfgget('crontasks')))
    if cfgget("cron") and cfgget('crontasks').lower() != 'n/a':
        from machine import Timer
        # INIT TIMER 1 IRQ with callback function wrapper
        lm_str = cfgget('crontasks')
        sample = int(cfgget("cronseq")/1000)
        timer = Timer(1)
        timer.init(period=int(cfgget("cronseq")), mode=Timer.PERIODIC,
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

    def __edge_exec(pin, resolver):
        """
        Prell filter / edge detection and execution
        :param pin: pin obj name
        :param resolver: callback resolver dict,  LM_cbf obj by pins {PinKey: [LM_cbf, prellTimer]}
        :return: None
        """
        pin = str(pin)
        # Get stored tick by pin - last executed
        last = resolver.get(pin)[1]
        # Calculate trigger diff in ms (from now)
        diff = ticks_diff(int(ticks_us() * 0.001), last)
        # console_write("[IRQ] Event {} - tick diff: {}".format(pin, diff))
        # Threshold between ext. irq evens
        if abs(diff) > resolver.get('prell_ms'):
            # [!] Execute LM(s)
            exec_lm_pipe_schedule(resolver.get(pin)[0])
            # Save now tick - last executed
            resolver[pin][1] = int(ticks_us() * 0.001)

    # External IRQ execution data set from node config
    # ((irq, trig, lm_cbf), (irq, trig, lm_cbf), (irq, trig, lm_cbf), ...)
    irqdata = ((cfgget("irq1"), cfgget("irq1_trig"), cfgget("irq1_cbf")),
               (cfgget("irq2"), cfgget("irq2_trig"), cfgget("irq2_cbf")),
               (cfgget("irq3"), cfgget("irq3_trig"), cfgget("irq3_cbf")),
               (cfgget("irq4"), cfgget("irq4_trig"), cfgget("irq4_cbf")))

    # [*] hardcopy parameters to be able to resolve cbf-s
    # cbf_resolver = {'Pin(1)': 'cbf;cbf', 'Pin(2)': 'cbf', ... + 'prell_ms': for example 300ms}
    cbf_resolver = {'prell_ms': cfgget("irq_prell_ms")}
    for i, data in enumerate(irqdata):
        irq, trig, lm_cbf = data
        console_write("[IRQ] EXTIRQ SETUP - EXT IRQ{}: {} TRIG: {}".format(i+1, irq, trig))
        console_write("|- [IRQ] EXTIRQ CBF: {}".format(lm_cbf))
        if irq:
            try:
                pin = physical_pin('irq{}'.format(i + 1))  # irq1, irq2, etc.
            except Exception as e:
                msg = '[ERR] EVENT IRQ{} IO error: {}'.format(i+1, e)
                pin = None
                console_write("|-- [!] {}".format(msg))
                errlog_add(msg)
            if pin:
                # [*] update resolver dict by pin number (available in irq callback):
                # PinKey: [CallbackFunction, PrellTimer]  (prell: contact recurrence - fake event filtering... :D)
                cbf_resolver['Pin({})'.format(pin)] = [lm_cbf, 0]
                trig = trig.strip().lower()
                # Init event irq with callback function wrapper
                # pin_obj = Pin(pin, Pin.IN, Pin.PULL_UP)            #TODO: expose built in resistor parameter ?
                pin_obj = Pin(pin, Pin.IN, Pin.PULL_DOWN)
                # [IRQ] - event type setup
                if trig == 'down':
                    # pin_obj.irq(trigger=Pin.IRQ_FALLING, handler=lambda pin: print("[down] {}:{}".format(pin, cbf_resolver[str(pin)])))
                    pin_obj.irq(trigger=Pin.IRQ_FALLING,
                                handler=lambda pin: __edge_exec(pin, cbf_resolver))
                    continue
                if trig == 'both':
                    # pin_obj.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=lambda pin: print("[both] {}:{}".format(pin, cbf_resolver[str(pin)])))
                    pin_obj.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
                                handler=lambda pin: __edge_exec(pin, cbf_resolver))
                    continue
                # Default - 'up'
                # pin_obj.irq(trigger=Pin.IRQ_RISING, handler=lambda pin: print("[up] {}:{}".format(pin, cbf_resolver[str(pin)])))
                pin_obj.irq(trigger=Pin.IRQ_RISING,
                            handler=lambda pin: __edge_exec(pin, cbf_resolver))

#################################################################
#                         INIT MODULE                           #
#################################################################


emergency_mbuff()
