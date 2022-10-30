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


def light_demo(modules, smooth=True, sample=10):
    verdict = [True, []]
    smooth_str = '[smooth]' if smooth else '[simple]'

    if 'LM_rgb' in modules:
        args = base_cmd() + [f'rgb random {smooth}'] * sample + ['rgb toggle False']
        print(args)
        delta_t = time.time()
        status_rgb, answer_rgb = socketClient.run(args)
        delta_t = round((time.time() - delta_t) / sample, 2)
        if status_rgb:
            msg = f"{smooth_str} rgb module random color func: {Colors.OK}OK{Colors.NC} [{delta_t}sec]"
            verdict[1].append(msg)
        else:
            msg = f"{smooth_str} rgb module random color func: {Colors.ERR}NOK{Colors.NC} [{delta_t}sec]"
            verdict[1].append(msg)
            verdict[0] &= False

    if 'LM_cct' in modules:
        args = base_cmd() + [f'cct random {smooth}'] * sample + ['cct toggle False']
        delta_t = time.time()
        status_cct, answer_cct = socketClient.run(args)
        delta_t = round((time.time() - delta_t) / sample, 2)
        if status_cct:
            msg = f"{smooth_str} cct module random color func: {Colors.OK}OK{Colors.NC} [{delta_t}sec]"
            verdict[1].append(msg)
        else:
            msg = f"{smooth_str} cct module random color func: {Colors.ERR}NOK{Colors.NC} [{delta_t}sec]"
            verdict[1].append(msg)
            verdict[0] &= False

    if 'LM_neopixel' in modules:
        args = base_cmd() + [f'neopixel random {smooth}'] * sample + ['neopixel toggle False']
        delta_t = time.time()
        status_neo, answer_neo = socketClient.run(args)
        delta_t = round((time.time() - delta_t) / sample, 2)
        if status_neo:
            msg = f"{smooth_str} neopixel module random color func: {Colors.OK}OK{Colors.NC} [{delta_t}sec]"
            verdict[1].append(msg)
        else:
            msg = f"{smooth_str} neopixel module random color func: {Colors.ERR}NOK{Colors.NC} [{delta_t}sec]"
            verdict[1].append(msg)
            verdict[0] &= False
    return verdict


def app(devfid=None):
    """
    devfid: selected device input
        send command(s) over socket connection [socketClient.run(args)]
        list load module commands and send in single connection
    """
    global DEVICE
    if devfid is not None:
        DEVICE = devfid

    # Get loaded modules
    args = base_cmd() + ['system module']
    status, modules = socketClient.run(args)
    print("status: {}\nanswer: {}".format(status, modules))

    if not status:
        print("Cannot get loaded modules from device: {}".format(modules))
        return

    verdict_smooth = light_demo(modules=modules, smooth=True, sample=5)
    verdict_simple = light_demo(modules=modules, smooth=False, sample=10)

    verdict = [verdict_smooth[0] & verdict_simple[0], verdict_smooth[1]+verdict_simple[1]]

    format_verdict = '\n'.join(verdict[1])
    print(f"\n{Colors.BOLD}###  Universal color change test [{'OK' if verdict[0] else 'NOK'}]  ##{Colors.NC}")
    print(f"{format_verdict}")


if __name__ == "__main__":
    app()
