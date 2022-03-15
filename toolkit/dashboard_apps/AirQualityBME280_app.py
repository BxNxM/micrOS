#!/usr/bin/env python3

import os
import sys
import time
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(MYPATH))
import socketClient

# FILL OUT
DEVICE = 'AirQualityPro'


def base_cmd():
    return ['--dev', DEVICE]


def app(devfid=None):
    global DEVICE
    if devfid is not None:
        DEVICE = devfid
    for k in range(0, 20):
        args = base_cmd() + ['bme280 measure']
        try:
            status, answer = socketClient.run(args)
            if status:
                print("|- [{}/20] OK".format(k+1))
            else:
                print("|- [{}/20] ERR".format(k+1))
            time.sleep(3)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    app()
