#!/usr/bin/env python3

import os
import atexit
from random import randint
MYPATH = os.path.dirname(os.path.abspath(__file__))

try:
    from ._app_base import AppBase
except:
    from _app_base import AppBase

CLIENT = None
CMD_PIPE_SEP = '<a>'
SERVO_CENTER_VAL = 77


def play_game(iteration=30, devfid=None):
    global CMD_PIPE_SEP
    for _ in range(iteration):
        piped_commands = []

        args = ['servo sduty {} '.format(SERVO_CENTER_VAL)]
        print("CMD: {}".format(args))
        args.append(CMD_PIPE_SEP)
        piped_commands += args

        for _ in range(randint(1, 6)):
            duty = randint(55, 100)
            args = ['servo sduty {duty} '.format(duty=duty)]
            print("\tCMD: {}".format(args))
            args.append(CMD_PIPE_SEP)
            piped_commands += args

        args += ['servo sduty {}'.format(SERVO_CENTER_VAL)]
        print("CMD: {}".format(args))
        piped_commands += args

        print("CMD PIPE: {}".format(piped_commands))
        CLIENT.run(piped_commands)


def deinit_servo():
    print("DEINIT SERVO, SET TO {} and DEINIT".format(SERVO_CENTER_VAL))
    args = ['servo sduty {}'.format(SERVO_CENTER_VAL)]
    CLIENT.run(args)


def app(devfid=None, pwd=None):
    global CLIENT
    CLIENT = AppBase(device=devfid, password=pwd)

    atexit.register(deinit_servo)
    play_game()
    deinit_servo()


if __name__ == "__main__":
    app()
