#!/usr/bin/env python3

import os
import sys
import atexit
from random import randint
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(MYPATH))
import socketClient

DEVICE = 'ImpiGamePro'
CMD_PIPE_SEP = '<a>'
SERVO_CENTER_VAL = 77


def base_cmd():
    return ['--dev', DEVICE]


def play_game(iteration=30, devfid=None):
    global CMD_PIPE_SEP
    for _ in range(iteration):
        piped_commands = []

        args = base_cmd() + ['servo sduty {} '.format(SERVO_CENTER_VAL)]
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
        socketClient.run(piped_commands)


def deinit_servo():
    print("DEINIT SERVO, SET TO {} and DEINIT".format(SERVO_CENTER_VAL))
    args = base_cmd() + ['servo sduty {}'.format(SERVO_CENTER_VAL)]
    socketClient.run(args)


def app(devfid=None):
    global DEVICE
    if devfid is not None:
        DEVICE = devfid
    atexit.register(deinit_servo)
    play_game()
    deinit_servo()


if __name__ == "__main__":
    app()
