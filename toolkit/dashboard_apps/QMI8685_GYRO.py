#!/usr/bin/env python3

import os
import sys
import json
import time
import multiprocessing as mp

MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../lib/'))

try:
    from ._app_base import AppBase
except ImportError:
    from _app_base import AppBase

def print_table(data):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{'Sensor':<10} {'X':>10} {'Y':>10} {'Z':>10}")
    for sensor in ['accel', 'gyro']:
        x, y, z = data[sensor]
        print(f"{sensor:<10} {x:10.2f} {y:10.2f} {z:10.2f}")
    if 'temp' in data:
        print(f"{'temp':<10} {data['temp']:>10.2f}")


def app(devfid=None, pwd=None):
    CLIENT = AppBase(device=devfid, password=pwd)
    measure_cmd = 'qmi8685 measure >json'

    mp.set_start_method('spawn', force=True)
    queue = mp.Queue()

    # Start GUI process
    from ._gyro_visualizer import visualizer_main
    p = mp.Process(target=visualizer_main, args=(queue,))
    p.start()

    try:
        for _ in range(10000):
            output = CLIENT.execute([measure_cmd])
            status, result = output[0], output[1]

            if status:
                try:
                    parsed = json.loads(result)
                    print_table(parsed)
                    queue.put(parsed)
                except Exception as e:
                    print(f"[Visualizer queue issue] {e}")
                    break
            else:
                print(f"[WARN] {result}")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Interrupted by user.")

    finally:
        if p.is_alive():
            p.terminate()
            p.join()



if __name__ == "__main__":
    app()
