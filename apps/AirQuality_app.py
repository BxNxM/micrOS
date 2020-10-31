#!/usr/bin/env python3

import os
import sys
import time
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../tools'))
import socketClient

# FILL OUT
DEVICE = 'airquality'


def base_cmd():
    return ['--dev', DEVICE]


def app(devfid=None):
    global DEVICE
    if devfid is not None:
        DEVICE = devfid
    while True:
        args = base_cmd() + ['air measure']
        try:
            socketClient.run(args)
            time.sleep(3)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    app()
