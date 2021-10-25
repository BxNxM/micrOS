#!/usr/bin/env python3

import os
import sys
import time
import random
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../tools'))
import socketClient

# FILL OUT
DEVICE = 'node01'


def base_cmd():
    return ['--dev', DEVICE]


class TestData:
    ERR_CNT = 0
    ERR_CNT_TOUT = 10
    EXEC_CNT = 0


def evaluate_test_data(answer_msg, test_cycle=None):
    expectation_in_data = 'NEOPIXEL SET TO'
    TestData.EXEC_CNT += 1
    if expectation_in_data in answer_msg:
        print("- [ OK ] |{}|".format(answer_msg))
    else:
        print("- [ ERR ] |{}|".format(answer_msg))
        TestData.ERR_CNT += 1
    if TestData.ERR_CNT >= TestData.ERR_CNT_TOUT:
        print("Error timeout.")
        sys.exit(1)
    print("Progress: {} err / {} / [{}]".format(TestData.ERR_CNT, TestData.EXEC_CNT, test_cycle))


def app(test_cycle=32, devfid=None):
    global DEVICE
    if devfid is not None:
        DEVICE = devfid
    for _ in range(0, test_cycle):
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)

        print("===========================")
        print("R: {}, G: {} B: {}".format(red, green, blue))
        command = base_cmd() + ['neopixel', 'neopixel {} {} {}'.format(red, green, blue)]
        print("CMD: {}".format(command))
        status, answer = socketClient.run(command)
        evaluate_test_data(answer, test_cycle)
        time.sleep(0.1)
    print("[i] Communication stability test with Lamp parameter configurations.")
    print("ERR: {} / ALL {} {}% success rate.".format(TestData.ERR_CNT, TestData.EXEC_CNT, round(100*(1-(TestData.ERR_CNT/TestData.EXEC_CNT)))))


if __name__ == "__main__":
    app()
