#!/usr/bin/env python3

"""
Generic webhook for socketClient that can invoke LoadModule calls remotely from any device.
Example: http://10.0.1.61:5000/webhooks/generic/TinyDevBoard+system+clock
"""

import sys, os
SCRIPT_NAME = os.path.basename(sys.argv[0])
SCRIPT_ARGS = sys.argv[1:]
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(os.path.dirname(MYPATH)))
import socketClient

def app():
    if len(SCRIPT_ARGS) > 1:
        device = SCRIPT_ARGS[0]
        cmd = ' '.join(SCRIPT_ARGS[1:])
        args = ['--dev', device, cmd]
        print(f'[WEBHOOK][GENERIC] cmd: {args}')
        return socketClient.run(args)
    return 'Missing device/module+function'


if __name__ == "__main__":
    print(app())
