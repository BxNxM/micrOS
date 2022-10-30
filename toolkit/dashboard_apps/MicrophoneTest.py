import sys, os
import subprocess
MYPATH = os.path.dirname(os.path.abspath(__file__))

DEVICE = "node01"


def app(devfid=None):
    """
    Wrapper function to start subprocess plotting... (threading limitation)
    """
    global DEVICE
    if devfid is not None:
        DEVICE = devfid
    result = subprocess.run([f'{sys.executable}', os.path.join(MYPATH, '_micPlotting.py'), DEVICE])
    print(result)
