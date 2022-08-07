"""
Module is responsible for
    - set up device
    - import and execute micrOS IoT FW

Designed by Marcell Ban aka BxNxM
"""

# This file is executed on every boot (including wake-boot from deepsleep)
try:
    import esp
    # Turn off esp debug msg-s over usb (UART)
    esp.osdebug(None)
except:
    print("[micrOS boot] non esp board")

from gc import enable
from micrOSloader import main

# Enable GC
enable()

# Start micrOS
main()
