"""
Easy reset for webrepl terminal
"""

from time import sleep
from uos import listdir
from machine import soft_reset, reset

print('Device reboot now, boot micrOSloader...')
sleep(1)

if "main.py" in listdir():
    soft_reset()
else:
    reset()
