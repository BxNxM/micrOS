#!/usr/bin/env python3

import os
import sys
import time
import random
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../tools'))
import socketClient

# FILL OUT
DEVICE = 'node01'
SMOOTH = True


def base_cmd():
    return ['--dev', DEVICE]


def app(devfid=None, test_cycle=32):
    global DEVICE
    if devfid is not None:
        DEVICE = devfid

    err_cnt = 0
    for cycle in range(1, test_cycle+1):
        red = random.randint(0, 1000)
        green = random.randint(0, 1000)
        blue = random.randint(0, 1000)
        # EDIT YOUR COMMAND
        if SMOOTH:
            args = base_cmd() + ['rgb', 'rgb {} {} {} True'.format(red, green, blue)]
        else:
            args = base_cmd() + ['rgb', 'rgb {} {} {}'.format(red, green, blue)]
        status, answer = socketClient.run(args)
        if status == 0 or 'R{}G{}B{}'.format(red, green, blue) in answer:
            print("[OK][{}/{}][{}] {}".format(cycle, test_cycle, err_cnt, answer))
        else:
            print("[ERROR][{}/30][{}] {}".format(cycle, test_cycle, err_cnt, answer))
            err_cnt += 1

    if err_cnt == 0:
        print("RESULT: 100% success rate")
    else:
        print("RESULT: {}% success rate".format((((test_cycle-err_cnt)/test_cycle)*100)))


if __name__ == "__main__":
    app()
