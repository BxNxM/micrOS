import time
import machine
import os
print('Device reboot now, boot micrOSloader...')
time.sleep(1)

if "main.py" in os.listdir():
    machine.soft_reset()
else:
    machine.reset()

