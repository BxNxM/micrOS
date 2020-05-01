#!/usr/bin/env python3

import os
import sys
import time
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../tools'))
import socketClient

# FILL OUT
DEVICE = 'node01'
BASE_CMD = ['--dev', DEVICE ]

def app():
    global DEVICE, BASE_CMD
    while True:
        args = BASE_CMD + ['air dht_measure <a> air getMQ135GasPPM']
        try:
            socketClient.run(args)
            time.sleep(5)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    app()
