#!/usr/bin/env python3

import os
import sys
import time
MYPATH = os.path.dirname(os.path.abspath(__file__))

try:
    from ._app_base import AppBase
except:
    from _app_base import AppBase

CLIENT = None


def app(devfid=None, pwd=None):
    global CLIENT
    CLIENT = AppBase(device=devfid, password=pwd)

    # EDIT YOUR COMMAND
    args = ['version']
    status, answer = CLIENT.run(args)
    print("[micrOS] {}: {}".format(CLIENT.get_device(), answer).upper())


if __name__ == "__main__":
    app()