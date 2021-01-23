#!/usr/bin/env python3

import os
import sys
import time
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../tools'))
import socketClient

# FILL OUT
DEVICE = 'node01'


def base_cmd():
    return ['--dev', DEVICE]


def app(devfid=None):
    """
    devfid: selected device input
        send command(s) over socket connection [socketClient.run(args)]
        <a> command separator in single connection
    """
    global DEVICE
    if devfid is not None:
        DEVICE = devfid
    # EDIT YOUR COMMAND
    args = base_cmd() + ['help', '<a>', 'version']
    status, answer = socketClient.run(args)


if __name__ == "__main__":
    app()
