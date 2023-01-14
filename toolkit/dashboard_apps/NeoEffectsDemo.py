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

    args = base_cmd() + ['task kill neoeffects.*', 'neopixel toggle False', 'neopixel toggle True']
    status, answer = socketClient.run(args)
    time.sleep(2)

    status, answer = socketClient.run(base_cmd() + ['neoeffects rainbow &&'])
    time.sleep(2)
    status, answer = socketClient.run(base_cmd() + ['task kill neoeffects.rainbow'])

    status, answer = socketClient.run(base_cmd() + ['neoeffects color 122 18 0'])

    status, answer = socketClient.run(base_cmd() + ['neoeffects cycle &&'])
    time.sleep(2)
    status, answer = socketClient.run(base_cmd() + ['task kill neoeffects.cycle'])

    status, answer = socketClient.run(base_cmd() + ['neoeffects meteor &&'])
    time.sleep(2)
    status, answer = socketClient.run(base_cmd() + ['task kill neoeffects.meteor'])

    status, answer = socketClient.run(base_cmd() + ['neoeffects fire &&'])
    time.sleep(2)
    status, answer = socketClient.run(base_cmd() + ['task kill neoeffects.fire'])

    time.sleep(1)

    status, answer = socketClient.run(base_cmd() + ['neoeffects random &&500'])

    status, answer = socketClient.run(base_cmd() + ['neoeffects cycle &&'])
    time.sleep(3)
    status, answer = socketClient.run(base_cmd() + ['task kill neoeffects.cycle'])

    status, answer = socketClient.run(base_cmd() + ['neoeffects meteor &&'])
    time.sleep(3)
    status, answer = socketClient.run(base_cmd() + ['task kill neoeffects.meteor'])

    status, answer = socketClient.run(base_cmd() + ['neoeffects fire &&'])
    time.sleep(3)
    status, answer = socketClient.run(base_cmd() + ['task kill neoeffects.fire'])

    status, answer = socketClient.run(base_cmd() + ['task kill neoeffects.random'])
    status, answer = socketClient.run(base_cmd() + ['neopixel color 122 18 0'])


if __name__ == "__main__":
    app()
