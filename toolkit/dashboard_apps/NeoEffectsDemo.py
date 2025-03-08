#!/usr/bin/env python3

import os
import time
MYPATH = os.path.dirname(os.path.abspath(__file__))

try:
    from ._app_base import AppBase
except:
    from _app_base import AppBase

CLIENT = None


def app(devfid=None, pwd=None):
    """
    devfid: selected device input
        send command(s) over socket connection [socketClient.run(args)]
        list load module commands and send in single connection
    """
    global CLIENT
    CLIENT = AppBase(device=devfid, password=pwd)

    args = ['task kill neoeffects.*', 'neopixel toggle False', 'neopixel toggle True']
    status, answer = CLIENT.run(args)
    time.sleep(2)

    status, answer = CLIENT.run(['neoeffects rainbow &&'])
    time.sleep(2)
    status, answer = CLIENT.run(['task kill neoeffects.rainbow'])

    status, answer = CLIENT.run(['neoeffects color 122 18 0'])

    status, answer = CLIENT.run(['neoeffects cycle &&'])
    time.sleep(2)
    status, answer = CLIENT.run(['task kill neoeffects.cycle'])

    status, answer = CLIENT.run(['neoeffects meteor &&'])
    time.sleep(2)
    status, answer = CLIENT.run(['task kill neoeffects.meteor'])

    status, answer = CLIENT.run(['neoeffects fire &&'])
    time.sleep(2)
    status, answer = CLIENT.run(['task kill neoeffects.fire'])

    time.sleep(1)

    status, answer = CLIENT.run(['neoeffects random &&500'])

    status, answer = CLIENT.run(['neoeffects cycle &&'])
    time.sleep(3)
    status, answer = CLIENT.run(['task kill neoeffects.cycle'])

    status, answer = CLIENT.run(['neoeffects meteor &&'])
    time.sleep(3)
    status, answer = CLIENT.run(['task kill neoeffects.meteor'])

    status, answer = CLIENT.run(['neoeffects fire &&'])
    time.sleep(3)
    status, answer = CLIENT.run(['task kill neoeffects.fire'])

    status, answer = CLIENT.run(['task kill neoeffects.random'])
    status, answer = CLIENT.run(['neopixel color 122 18 0'])


if __name__ == "__main__":
    app()
