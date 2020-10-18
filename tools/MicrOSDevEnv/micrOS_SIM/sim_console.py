import sys
import os
MYPATH = os.path.dirname(os.path.abspath(__file__))
DEV_ENV_DIR = os.path.dirname(MYPATH)
sys.path.append(DEV_ENV_DIR)
from TerminalColors import Colors


def console(msg, end='\n', skip_tmp_msgs=True):
    if end == '\r' and skip_tmp_msgs:
        return
    if end == '\r':
        print(' '*100, end='\r')
    print("{}[SIM]{} {}".format(Colors.OKGREEN, Colors.NC, msg), end=end)


if __name__ == "__main__":
    console("TEST")