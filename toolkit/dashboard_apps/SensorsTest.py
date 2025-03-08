#!/usr/bin/env python3

import os
MYPATH = os.path.dirname(os.path.abspath(__file__))

try:
    from ._app_base import AppBase
except:
    from _app_base import AppBase

CLIENT = None

def measure(args, req_cnt=5):
    verdict = f"Measure with {args[0]}"
    print(verdict)
    err_cnt = 0
    for k in range(0, req_cnt):
        try:
            status, answer = CLIENT.run(args)
            if status:
                print(f"\t|- [{k+1}/{req_cnt}] OK")
            else:
                print(f"\t|- [{k+1}/{req_cnt}] ERR")
                err_cnt += 1
        except KeyboardInterrupt:
            break
    verdict = f"{verdict}\t" + "[OK]" if err_cnt == 0 else f"[ERR] {err_cnt}"
    return verdict


def app(devfid=None, pwd=None):
    global CLIENT
    CLIENT = AppBase(device=devfid, password=pwd)
    report = []

    state, result = CLIENT.run(['modules'])
    if not state:
        return "Error getting models."

    if "bme280" in result:
        args = ['bme280 measure']
        report.append(measure(args))

    if "dht22" in result:
        args = ['dht22 measure']
        report.append(measure(args))

    if "dht11" in result:
        args = ['dht22 measure']
        report.append(measure(args))

    if "ds18" in result:
        args = ['ds18 measure']
        report.append(measure(args))

    print(f"\n======== Sensor test report {CLIENT.get_device()} ========")
    for r in report:
        print(f"\t{r}")

if __name__ == "__main__":
    app()
