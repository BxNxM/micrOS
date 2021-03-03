"""
This module loads before Network setup!

Module is responsible for collect the additional
feature definition dedicated to micrOS framework.

Boot phase execution based on config
- initialize / preload modules to memory

Profiling info
- free memory monitoring between seperated phases
- memory block usage

Designed by Marcell Ban aka BxNxM
"""

#################################################################
#                           IMPORTS                             #
#################################################################
from sys import platform
from ConfigHandler import cfgget, console_write
from InterpreterCore import execLMPipe
from micropython import mem_info
from machine import freq

#################################################################
#                          FUNCTIONS                            #
#################################################################


def bootup_hook():
    """
    Executes when system boots up.
    """
    # Execute LMs from boothook config parameter
    console_write("[BOOT HOOKS] EXECUTION ...")
    bootasks = cfgget('boothook')
    if bootasks is not None and bootasks.lower() != 'n/a':
        console_write("|-[BOOT HOOKS] TASKS: {}".format(bootasks))
        if execLMPipe(bootasks):
            console_write("|-[BOOT HOOKS] DONE")
        else:
            console_write("|-[BOOT HOOKS] ERROR")

    # Set boostmd (boost mode)
    if cfgget('boostmd') is True:
        console_write("[BOOT HOOKS] Set up CPU 16MHz/24MHz - boostmd: {}".format(cfgget('boostmd')))
        if platform == 'esp8266': freq(160000000)
        if platform == 'esp32': freq(240000000)
    else:
        console_write("[BOOT HOOKS] Set up CPU 8MHz - boostmd: {}".format(cfgget('boostmd')))
        freq(80000000)


def profiling_info(label=""):
    """
    Runtime memory measurements
    """
    if cfgget('dbg'):
        console_write("{} [PROFILING INFO] - {} {}".format('~'*5, label, '~'*5))
        mem_info()
        console_write("~"*30)
