# VERSION 1.0
from machine import Pin
from time import sleep

#################################################################
#          _____ _                _____ _____                   #
#         / ____| |        /\    / ____/ ____|                  #
#        | |    | |       /  \  | (___| (___                    #
#        | |    | |      / /\ \  \___ \\___ \                   #
#        | |____| |____ / ____ \ ____) |___) |                  #
#         \_____|______/_/    \_\_____/_____/                   #
#################################################################
try:
    pled = Pin(16, Pin.OUT)
except:
    pled = None

def toggle():
    if pled is not None:
        if pled.value() == 0:
            pled.value(1)
        elif pled.value() == 1:
            pled.value(0)
        else:
            print("UNKNOWN STATUS")
    else:
        print("pled initialization error...")
