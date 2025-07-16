#!/usr/bin/env python3

import os
import sys
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../lib/'))
from TerminalColors import Colors

import json, time

try:
    from ._app_base import AppBase
except:
    from _app_base import AppBase

CLIENT = None


def print_table(data):
    # Clear display
    os.system('cls' if os.name == 'nt' else 'clear')

    # Print table header
    print(f"{'Sensor':<10} {'X':>10} {'Y':>10} {'Z':>10}")

    # Print accel and gyro values
    for sensor in ['accel', 'gyro']:
        x, y, z = data[sensor]
        print(f"{sensor:<10} {x:10.2f} {y:10.2f} {z:10.2f}")

    # Handle temp separately if needed
    if 'temp' in data:
        print(f"{'temp':<10} {data['temp']:>10.2f}")


def app(devfid=None, pwd=None):
    """
    devfid: selected device input
        send command(s) over socket connection [socketClient.run(args)]
        list load module commands and send in single connection
    """
    global CLIENT
    CLIENT = AppBase(device=devfid, password=pwd)

    measure_cmd = 'qmi8685 measure >json'
    for _ in range(0, 10000):
        print("-"*80)
        output = CLIENT.execute([measure_cmd])
        status = output[0]
        result = output[1]
        if status:
            parsed_result = json.loads(result)
            print_table(parsed_result)
        else:
            print(f"{Colors.WARN}[{status}]{Colors.NC} {result}")


if __name__ == "__main__":
    app()
