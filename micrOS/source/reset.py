import time
import machine
import os
print('Device reboot now, boot micrOS mode...')
time.sleep(1)

if "main.py" in os.listdir():
    machine.soft_reset()
else:
    machine.reset()

