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


def test():
    print(f"{Colors.BOLD}1. Turn Channels OFF{Colors.NC}")
    # Turn OFF all outputs (+ initialize all modules) [6 channel]
    cmd_off_all = ['rgb rgb 1 1 1', '<a>', 'rgb toggle False', '<a>',
                   'cct white 1 1', '<a>', 'cct toggle False', '<a>',
                   'dimmer set_value 1', '<a>', 'dimmer toggle False']
    status = send_cmd(cmd_off_all)

    print(f"{Colors.BOLD}2. Turn RGB Channels ON effect{Colors.NC}")
    # RGB ON ONE-BY-ONE EFFECT [3 channel]
    cmd_on_rgb = ['rgb rgb 900 0 0', '<a>',
                  'rgb rgb 0 900 0', '<a>',
                  'rgb rgb 0 0 900', '<a>',
                  'rgb rgb 0 0 1', '<a>', 'rgb rgb 0 0 0']
    status &= send_cmd(cmd_on_rgb)

    print(f"{Colors.BOLD}3. Turn CCT Channels ON effect{Colors.NC}")
    # CCT ON ONE-BY-ONE EFFECT [2 channel]
    cmd_on_cct = ['cct white 0 900', '<a>',
                  'cct white 900 0', '<a>',
                  'cct white 1 0', '<a>', 'cct white 0 0']
    status &= send_cmd(cmd_on_cct)

    print(f"{Colors.BOLD}4. Turn Dimmer Channel ON effect{Colors.NC}")
    # DIMMER ON EFFECT [1 channel]
    cmd_on_dimmer = ['dimmer set_value 900', '<a>',
                     'dimmer set_value 1', '<a>', 'dimmer set_value 0']
    status &= send_cmd(cmd_on_dimmer)

    print(f"{Colors.BOLD}5. Turn ALL Channels ON{Colors.NC}")
    # ON ALL CHANNELS [6 channel]
    cmd_on_all = ['rgb rgb 900 900 900', '<a>',
                   'cct white 900 900', '<a>',
                   'dimmer set_value 900']
    status &= send_cmd(cmd_on_all)
    time.sleep(2)

    print(f"{Colors.BOLD}6. Turn ALL Channels OFF{Colors.NC}")
    # OFF ALL CHANNELS [6 channel]
    cmd_off_all = ['rgb toggle False', '<a>',
                   'cct toggle False', '<a>',
                   'dimmer toggle False']
    status &= send_cmd(cmd_off_all)

    # RETURN VERDICT
    return status


def app(devfid=None):
    """
    devfid: selected device input
        send command(s) over socket connection [socketClient.run(args)]
        <a> command separator in single connection
    """
    global DEVICE
    if devfid is not None:
        DEVICE = devfid
    verdict = test()
    col = Colors.OK if verdict else Colors.ERR
    print("VERDICT: {}{}{}".format(col, verdict, Colors.NC))


def send_cmd(cmd_list):
    args = base_cmd() + cmd_list
    status, answer = socketClient.run(args)
    col = Colors.OK if status else Colors.ERR
    print("CMDS: {}\n{}{}{}\n".format(cmd_list, col, answer, Colors.NC))
    return status


if __name__ == "__main__":
    app()
