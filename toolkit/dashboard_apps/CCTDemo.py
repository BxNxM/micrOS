#!/usr/bin/env python3

import os
import sys
import time
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(MYPATH))
import socketClient
sys.path.append(os.path.join(MYPATH, '../lib/'))
from TerminalColors import Colors

# FILL OUT
DEVICE = 'node01'


def base_cmd():
    return ['--dev', DEVICE]


def app(devfid=None):
    """
    devfid: selected device input
        send command(s) over socket connection [socketClient.run(args)]
        list load module commands and send in single connection
    """
    global DEVICE
    if devfid is not None:
        DEVICE = devfid

    status, answer = socketClient.run(base_cmd() + ['cct white 50 400',
                                                    'cct brightness 50'])
    status, answer = socketClient.run(base_cmd() + ['cct brightness 100', 'cct brightness 20',
                                                    'cct brightness 60'])
    status, answer = socketClient.run(base_cmd() + ['cct white 400 50',
                                                    'cct brightness 100', 'cct brightness 20'])
    status, answer = socketClient.run(base_cmd() + ['cct white 600 700',
                                                    'cct white 50 300'])


if __name__ == "__main__":
    app()
