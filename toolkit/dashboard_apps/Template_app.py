#!/usr/bin/env python3

import os
import sys
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../lib/'))
from TerminalColors import Colors

try:
    from ._app_base import AppBase
except:
    from _app_base import AppBase

CLIENT = None

def app(devfid=None, pwd=None):
    """
    devfid: selected device input
        send command(s) over socket connection [socketClient.run(args)]
        list load module commands and send in single connection
    """
    global CLIENT
    CLIENT = AppBase(device=devfid, password=pwd)

    output = CLIENT.execute(['help', 'version'])
    status = output[0]
    result = output[1]
    print(f"{Colors.WARN}[{status}]{Colors.NC} {result}")


if __name__ == "__main__":
    app()
