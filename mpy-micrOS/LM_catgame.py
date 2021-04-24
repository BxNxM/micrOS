from random import randint
from LM_servo import sduty
from time import sleep


def game(repeat=10):
    sduty(75)
    for _ in range(0, repeat):
        sduty(randint(55, 95))
        sleep(randint(0, 2))
    sduty(75)
    return 'Game was over'


def stop():
    return sduty(75)


#######################
# LM helper functions #
#######################

def lmdep():
    return 'LM_servo'


def help():
    return 'game repeat=10', 'stop', 'lmdep'
