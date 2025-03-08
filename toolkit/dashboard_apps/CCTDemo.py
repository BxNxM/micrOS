#!/usr/bin/env python3

import os
import sys
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../lib/'))

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

    status, answer = CLIENT.run(['cct white 50 400',
                                                    'cct brightness 50'])
    status, answer = CLIENT.run(['cct brightness 100', 'cct brightness 20',
                                                    'cct brightness 60'])
    status, answer = CLIENT.run(['cct white 400 50',
                                                    'cct brightness 100', 'cct brightness 20'])
    status, answer = CLIENT.run(['cct white 600 700',
                                                    'cct white 50 300'])


if __name__ == "__main__":
    app()
