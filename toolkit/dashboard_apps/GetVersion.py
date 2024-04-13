#!/usr/bin/env python3

import os
import sys
import time
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(MYPATH))
import socketClient

# FILL OUT
DEVICE = 'node01'
PASSWD = None


def base_cmd():
    if PASSWD is None:
        return ['--dev', DEVICE]
    return ['--dev', DEVICE, '--password', PASSWD]



def app(devfid=None, pwd=None):
    global DEVICE, PASSWD
    if devfid is not None:
        DEVICE = devfid
    if pwd is not None:
        PASSWD = pwd
    # EDIT YOUR COMMAND
    args = base_cmd() + ['version']
    status, answer = socketClient.run(args)
    print("[micrOS] {}: {}".format(DEVICE, answer).upper())


if __name__ == "__main__":
    app()