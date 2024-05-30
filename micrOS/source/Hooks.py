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
from Config import cfgget, cfgput
from microIO import detect_platform
from Debug import console_write
from Tasks import exec_lm_pipe
from micropython import mem_info
from machine import freq

#################################################################
#                          FUNCTIONS                            #
#################################################################


def bootup():
    """
    Executes when system boots up.
    """
    # Execute LMs from boothook config parameter
    console_write("[BOOT] EXECUTION ...")
    bootasks = cfgget('boothook')
    bootasks = _migrate(bootasks)                # load_n_init -> load migration (simplify)
    if bootasks is not None and bootasks.lower() != 'n/a':
        console_write(f"|-[BOOT] TASKS: {bootasks}")
        if exec_lm_pipe(bootasks):
            console_write("|-[BOOT] DONE")
        else:
            console_write("|-[BOOT] ERROR")

    # Set boostmd (boost mode)
    platform = detect_platform()
    if cfgget('boostmd') is True:
        console_write(f"[BOOT HOOKS] Set up CPU high Hz - boostmd: {cfgget('boostmd')}")
        if platform == 'esp32c3':
            freq(160_000_000)   # 160 Mhz (max)
        elif 'esp32' in platform:
            freq(240_000_000)   # 240 Mhz (max)
    else:
        console_write(f"[BOOT HOOKS] Set up CPU low Hz - boostmd: {cfgget('boostmd')}")
        if platform == 'esp32c3':
            freq(80_000_000)   # 80 Mhz / Half the max CPU clock
        elif 'esp32' in platform:
            freq(160_000_000)   # 160 Mhz / Half the max CPU clock


def profiling_info(label=""):
    """
    Runtime memory measurements
    """
    if cfgget('dbg'):
        console_write(f"{'~'*5} [PROFILING INFO] - {label} {'~'*5}")
        mem_info()
        console_write("~"*30)

def _migrate(bootstr):
    """
    OBSOLETE load_n_init -- REMOVE AT 2023.12
    Use load instead
    - auto replace in boothook param
    """
    if 'load_n_init' in bootstr:
        console_write("[MIGRATE] load_n_init -> load")
        bootstr = bootstr.replace('load_n_init', 'load')
        cfgput('boothook', bootstr)
    return bootstr

