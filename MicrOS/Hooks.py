"""
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
from InterpreterCore import execute_LM_function_Core
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
    console_write("[BOOT HOOKS] EXECUTION...")
    if cfgget('boothook') is not None and cfgget('boothook').lower() != 'n/a':
        for shell_cmd in (cmd.strip() for cmd in tuple(cfgget('boothook').split(';')) if len(cmd.split()) > 1):
            console_write("|-[BOOT HOOKS] SHELL EXEC: {}".format(shell_cmd))
            try:
                state = execute_LM_function_Core(shell_cmd.split())
                console_write("|-[BOOT HOOKS] state: {}".format(state))
            except Exception as e:
                console_write("|--[BOOT HOOKS] error: {}".format(e))

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
    else:
        console_write("[PROFILING INFO] SKIP dbg:{}".format(cfgget('dbg')))
