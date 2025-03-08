#!/usr/bin/env python3

import os
MYPATH = os.path.dirname(os.path.abspath(__file__))

try:
    from ._app_base import AppBase
except:
    from _app_base import AppBase

CLIENT = None


def app(devfid=None, pwd=None, itr=80):
    global CLIENT
    CLIENT = AppBase(device=devfid, password=pwd)

    # EDIT YOUR COMMAND
    cmd_list = []
    for k in range(0, itr, 2):
        cmd_list += ['dimmer set_value {} smooth=False >json'.format(k)]
    CLIENT.run(cmd_list)

    cmd_list = []
    for k in range(itr, 0, -2):
        cmd_list += ['dimmer set_value {} smooth=False >json'.format(k)]
    CLIENT.run(cmd_list)

    cmd_list = ['dimmer set_value 300', 'dimmer toggle False', 'dimmer toggle True']
    CLIENT.run(cmd_list)


if __name__ == "__main__":
    app()
