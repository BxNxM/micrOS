#!/usr/bin/env python3

import os
import sys
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(MYPATH))
import socketClient


# FILL OUT
DEVICE = 'CamLed'


def base_cmd():
    return ['--dev', DEVICE]


def app(devfid=None, itr=80):
    global DEVICE
    if devfid is not None:
        DEVICE = devfid
    # EDIT YOUR COMMAND
    cmd_list = []
    for k in range(0, itr, 2):
        cmd_list += ['dimmer set_value {} smooth=False >json'.format(k)]
    execute(cmd_list)

    cmd_list = []
    for k in range(itr, 0, -2):
        cmd_list += ['dimmer set_value {} smooth=False >json'.format(k)]
    execute(cmd_list)

    cmd_list = ['dimmer set_value 300', 'dimmer toggle False', 'dimmer toggle True']
    execute(cmd_list)


def execute(cmd_list):
    cmd_args = base_cmd() + cmd_list
    print("DIMMER TEST: {}".format(cmd_args))
    socketClient.run(cmd_args)


if __name__ == "__main__":
    app()
