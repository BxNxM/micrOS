#!/usr/bin/env python3

import os
import sys
import time
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../tools'))
import socketClient

# FILL OUT
DEVICE = 'slim01'
BASE_CMD = ['--dev', DEVICE]


def app():
    global DEVICE, BASE_CMD
    # EDIT YOUR COMMAND
    args = BASE_CMD + ['help']
    socketClient.run(args)


if __name__ == "__main__":
    app()
