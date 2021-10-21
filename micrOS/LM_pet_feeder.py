from LM_servo import sduty, deinit
from LM_stepper import step, standby
from utime import sleep_ms


def portion(repeat=1, posmin=65, posmax=97):
    # Run portion sequence
    for _ in range(0, repeat):
        # Run pos fill up
        for pos in range(posmin, posmax):
            sduty(pos)
            sleep_ms(10)
        sleep_ms(500)
        # Run pos food out
        for pos in range(posmax, posmin, -1):
            sduty(pos)
            sleep_ms(15)
    deinit()
    return 'Portion {} was served'.format(repeat)


def portion_new(count=1, forward=135, back=10):
    for _ in range(count):
        # portion move
        step(forward)
        # Safety anti-block solution?
        step(-back)
        step(back)
        step(-back)
        step(back)


def lmdep():
    return 'LM_servo', 'LM_stepper'


def help():
    return 'portion repeat=1', '<-servo control',  'portion_new count=1', '<-stepper control'
