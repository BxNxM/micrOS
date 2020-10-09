"""
Module is responsible for
    - set up device
    - import and execute micrOS IoT FW

Designed by Marcell Ban aka BxNxM
"""

# This file is executed on every boot (including wake-boot from deepsleep)
import esp
from gc import enable
from micrOSloader import main

esp.osdebug(None)

# disable REPL on UART(0)
# uos.dupterm(None, 1)

# Enable GC
enable()

# Start micrOS
main()
