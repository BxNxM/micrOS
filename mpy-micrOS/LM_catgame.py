from random import randint
from LM_servo import sduty
from time import sleep


def game(iter=10):
    sduty(75)
    for _ in range(0, iter):
        sduty(randint(55, 95))
        sleep(randint(0, 2))
    sduty(75)
    return 'Game was over'


def stop():
    return sduty(75)


def help():
    return 'game iter=10', 'stop', 'Dependency: LM_servo sduty'
