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
from ConfigHandler import cfgget
from Debug import console_write
from InterpreterCore import exec_lm_pipe_schedule
from LogicalPins import physical_pin

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
#                  EVENT/EXTERNAL INTERRUPT(S)                  #
#################################################################
# trigger=Pin.IRQ_FALLING   signal HIGH to LOW
# trigger=Pin.IRQ_RISING    signal LOW to HIGH
#################################################################


def initEventIRQs():
    """
    EVENT INTERRUPT CONFIGURATION - multiple
    """
    irqdata = ((cfgget("irq1"), cfgget("irq1_trig"), cfgget("irq1_cbf")),
               (cfgget("irq2"), cfgget("irq2_trig"), cfgget("irq2_cbf")))

    # [*] hardcopy parameters to be able to resolve cbf-s
    cbf_resolver = {}
    for i, data in enumerate(irqdata):
        irq, trig, cbf = data
        console_write("[IRQ] EXTIRQ SETUP - EXT IRQ{}: {} TRIG: {}".format(i+1, irq, trig))
        console_write("|- [IRQ] EXTIRQ CBF: {}".format(cbf))
        pin = physical_pin('irq{}'.format(i+1))       # irq1, irq2, etc.
        if irq and pin:
            # [*] update cbf dict by pin number (available in irq callback)
            cbf_resolver['Pin({})'.format(pin)] = cbf
            trig = trig.strip().lower()
            # Init event irq with callback function wrapper
            # pin_obj = Pin(pin, Pin.IN, Pin.PULL_UP)            # TODO: expose parameter
            pin_obj = Pin(pin, Pin.IN, Pin.PULL_DOWN)
            # [IRQ] - event type setup
            if trig == 'down':
                # pin_obj.irq(trigger=Pin.IRQ_FALLING, handler=lambda pin: print("[down] {}:{}".format(pin, cbf_resolver[str(pin)])))
                pin_obj.irq(trigger=Pin.IRQ_FALLING,
                            handler=lambda pin: exec_lm_pipe_schedule(cbf_resolver[str(pin)]))
                continue
            if trig == 'both':
                # pin_obj.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=lambda pin: print("[both] {}:{}".format(pin, cbf_resolver[str(pin)])))
                pin_obj.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING,
                            handler=lambda pin: exec_lm_pipe_schedule(cbf_resolver[str(pin)]))
                continue
            # Default
            # pin_obj.irq(trigger=Pin.IRQ_RISING, handler=lambda pin: print("[up] {}:{}".format(pin, cbf_resolver[str(pin)])))
            pin_obj.irq(trigger=Pin.IRQ_RISING,
                        handler=lambda pin: exec_lm_pipe_schedule(cbf_resolver[str(pin)]))

#################################################################
#                         INIT MODULE                           #
#################################################################


emergency_mbuff()
