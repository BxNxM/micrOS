import sys, os
import subprocess
MYPATH = os.path.dirname(os.path.abspath(__file__))


def app(devfid=None, pwd=None):
    """
    Wrapper function to start subprocess plotting... (threading limitation)
    """
    result = subprocess.run([f'{sys.executable}', os.path.join(MYPATH, '_capture.py'), devfid])
    print(result)
