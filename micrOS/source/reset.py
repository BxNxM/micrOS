from os import listdir
from time import sleep
from machine import soft_reset, reset

print('Device reboot now, boot micrOSloader...')
sleep(1)

if "main.py" in listdir():
    soft_reset()
else:
    reset()
