from LM_servo import sduty, deinit
from time import sleep_ms


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


def lmdep():
    return 'LM_servo'


def help():
    return 'portion repeat=1'
