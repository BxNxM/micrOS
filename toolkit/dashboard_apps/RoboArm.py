#!/usr/bin/env python3

try:
    from ._app_base import AppBase
except:
    from _app_base import AppBase


CLIENT = None
__TEST_DATA = {'ok': 0, 'err': 0}


def test_eval(state, msg):
    if state:
        print(f"[OK] return: {msg}")
        __TEST_DATA['ok'] += 1
    else:
        print(f"[ERR] return: {msg}")
        __TEST_DATA['err'] += 1


def app(devfid=None, pwd=None):
    """
    devfid: selected device input
        send command(s) over socket connection [socketClient.run(args)]
        <a> command separator in single connection
    """
    global CLIENT
    CLIENT = AppBase(device=devfid, password=pwd)

    def home():
        args = ['roboarm control 75 70']
        status, answer = CLIENT.run(args)
        test_eval(status, answer)

    def switch(state=False):
        args = ['switch set_state {}'.format(state)]
        status, answer = CLIENT.run(args)
        print(answer)

    home()
    switch(True)

    args = ['roboarm control 40 40 speed_ms=7']
    status, answer = CLIENT.run(args)
    test_eval(status, answer)

    home()

    args = ['roboarm control 115 115']
    status, answer = CLIENT.run(args)
    test_eval(status, answer)

    args = ['roboarm control 40 115']
    status, answer = CLIENT.run(args)
    test_eval(status, answer)

    args = ['roboarm control 115 40']
    status, answer = CLIENT.run(args)
    test_eval(status, answer)

    args = ['roboarm control 40 40']
    status, answer = CLIENT.run(args)
    test_eval(status, answer)

    # Move back to home pos
    args = ['roboarm control 75 70 speed_ms=3']
    status, answer = CLIENT.run(args)
    test_eval(status, answer)

    switch(False)

    print("[Roboarm] success rate: {} %".format(round(__TEST_DATA['ok']/(__TEST_DATA['ok']+__TEST_DATA['err'])*100), 2))


if __name__ == "__main__":
    app()
