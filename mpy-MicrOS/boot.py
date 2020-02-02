# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(None)
#import uos, machine
#uos.dupterm(None, 1) # disable REPL on UART(0)
#import webrepl
#webrepl.start()

from machine import freq
freq(160000000)

from gc import collect, mem_free
collect()
mem_free()
