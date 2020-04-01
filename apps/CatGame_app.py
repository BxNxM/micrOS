#!/usr/bin/env python3

import os
import sys
from random import randint
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../tools'))
import socketClient

DEVICE = 'ImpiGame'
BASE_CMD = ['--dev', DEVICE ]
CMD_PIPE_SEP = '<a>'

def app(iteration=60):
    global DEVICE, BASE_CMD, CMD_PIPE_SEP
    for _ in range(iteration):
        piped_commands = []

        args = BASE_CMD + ['servo', 'Servo(40)']
        print("CMD: {}".format(args))
        args.append(CMD_PIPE_SEP)
        piped_commands += args

        for _ in range(randint(1, 6)):
            duty = randint(50, 110)
            args = ['servo', 'Servo({duty})'.format(duty=duty)]
            print("\tCMD: {}".format(args))
            args.append(CMD_PIPE_SEP)
            piped_commands += args

        args = ['servo', 'Servo(120)']
        print("\tCMD: {}".format(args))
        args.append(CMD_PIPE_SEP)
        piped_commands += args

        args = ['servo', 'Servo(80)']
        print("CMD: {}".format(args))
        args.append(CMD_PIPE_SEP)
        piped_commands += args

        print("CMD PIPE: {}".format(piped_commands))
        socketClient.run(piped_commands)

    args = BASE_CMD + ['servo', 'Servo_deinit']
    socketClient.run(args)


if __name__ == "__main__":
    app()
