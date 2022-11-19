import sys
import os
#MYPATH = os.path.dirname(os.path.abspath(__file__))
#DEV_ENV_DIR = os.path.dirname(MYPATH)
#sys.path.append(DEV_ENV_DIR)

print("Module [sim_console] path: {} __package__: {} __name__: {}".format(sys.path[0], __package__, __name__))

PACKAGE = '' if __package__ is None else str(__package__).replace('.', os.sep)
MYPATH = os.path.join(sys.path[0], PACKAGE)
LIB = os.path.join(MYPATH, 'toolkit/lib')
sys.path.append(LIB)
try:
    from TerminalColors import Colors
except Exception as e:
    print("TerminalColors import error: {}".format(e))
    Colors = None

def console(msg, end='\n', skip_tmp_msgs=True):
    if end == '\r' and skip_tmp_msgs:
        return
    if end == '\r':
        print(' '*100, end='\r')
    if Colors is None:
        print("[SIM] {}".format(msg), end=end)
    else:
        print("{}[SIM]{} {}".format(Colors.OKGREEN, Colors.NC, msg), end=end)


if __name__ == "__main__":
    console("TEST")
