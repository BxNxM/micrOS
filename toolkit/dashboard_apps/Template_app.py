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
PASSWD = None

def base_cmd():
    if PASSWD is None:
        return ['--dev', DEVICE]
    return ['--dev', DEVICE, '--password', PASSWD]

def run_command(cmd):
    # EDIT YOUR COMMAND
    args = base_cmd() + cmd
    status, answer = socketClient.run(args)
    return status, answer


def app(devfid=None, pwd=None):
    """
    devfid: selected device input
        send command(s) over socket connection [socketClient.run(args)]
        list load module commands and send in single connection
    """
    global DEVICE, PASSWD
    if devfid is not None:
        DEVICE = devfid
    if pwd is not None:
        PASSWD = pwd

    status, answer = run_command(['help', 'version'])


if __name__ == "__main__":
    app()
