# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(None)
#uos.dupterm(None, 1) # disable REPL on UART(0)

from machine import freq
freq(160000000)

from gc import enable
enable()
