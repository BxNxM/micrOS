#!/usr/bin/env python3

import os
import sys
import time
import random
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../lib/'))
from TerminalColors import Colors

try:
    from ._app_base import AppBase
except:
    from _app_base import AppBase

CLIENT = None


def test_random_colors(test_len=8, smooth=False):
    main_function = 'rgb color'
    # generate color list
    color_list = []
    for cycle in range(1, test_len+1):
        red = random.randint(0, 1000)
        green = random.randint(0, 1000)
        blue = random.randint(0, 1000)
        color_list.append((red, green, blue))

    # Generate command
    cmd_list_str = " <a> ".join(["{} {} {} {} {} >json".format(main_function, k[0], k[1], k[2], smooth) for k in color_list])
    args = [cmd_list_str]
    print("{} Generated command {} - multi message single connection single connection: {} r g b {}\n{}".format(Colors.HEADER, Colors.NC, main_function, smooth, args))

    start_t = time.time()
    # SEND MESSSAGE OVER micrOS client
    status, answer = CLIENT.run(args)
    delta_t = round((time.time() - start_t)/test_len, 1)

    #Evaluate last message
    print("status: {}\nanswer: {}".format(status, answer))

    if status is True:
        if '"R": {}'.format(color_list[-1][0]) in answer and \
            '"G": {}'.format(color_list[-1][1]) in answer and \
            '"B": {}'.format(color_list[-1][2]) in answer:
            return True, 'Communication was {}OK{}, msg deltaT: {}'.format(Colors.OK, Colors.NC, delta_t)
    else:
        return False, 'Communication was {}NOK{}, msg deltaT: {}'.format(Colors.ERR, Colors.NC, delta_t)


def test_toogle():
    main_function = 'rgb toggle'
    args_on = [f'{main_function} True >json']
    args_toggle = [f'{main_function} >json']

    # SEND MESSSAGE OVER micrOS client
    status, answer = CLIENT.run(args_on)
    if status and '"S": 1' in answer:
        # SEND MESSSAGE OVER micrOS client
        status, answer = CLIENT.run(args_toggle)
        if status and '"S": 0' in answer:
            return True, '{} works {}OK{}'.format(main_function, Colors.OK, Colors.NC)
    return False, '{} not works {}NOK{}: {}'.format(main_function, Colors.ERR, Colors.NC, answer)


def test_brightness():
    main_function = 'rgb brightness'
    args_10 = [f'{main_function} 10 >json']
    args_50 = [f'{main_function} 50 >json']
    args_actual_br = [f'{main_function} >json']

    status, answer = CLIENT.run(args_10)
    if status:
        status, answer = CLIENT.run(args_50)
        if status:
            status, answer = CLIENT.run(args_actual_br)
            if status and "50.0 %" in answer:
                return True, "{} function {}OK{} (50.0 % == {})".format(main_function, Colors.OK, Colors.NC, answer)
    return False, "{} function {}NOK{} (50.0 % == {})".format(main_function, Colors.ERR, Colors.NC, answer)


def app(devfid=None, pwd=None):
    global CLIENT
    CLIENT = AppBase(device=devfid, password=pwd)

    test_pool = { 'Color change test': test_random_colors(test_len=8, smooth=False),
                  'Color smooth test': test_random_colors(test_len=4, smooth=True),
                  'Toggle func. test': test_toogle(),
                  'Brightness test  ': test_brightness()}

    print("\n{}RGB module test verdict{}".format(Colors.HEADER, Colors.NC))
    print("-----------------------")
    pass_cnt = 0
    for k, v in test_pool.items():
        if v is not None and v[0]:
            verdict = v[1]
            pass_cnt += 1
        else:
            verdict = None
        print("\t{} - {}".format(k, verdict))
    print("{}{} % success rate.{}".format(Colors.BOLD, round(round((pass_cnt/len(test_pool))*100)), Colors.NC))

if __name__ == "__main__":
    app()
