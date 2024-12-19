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
from Debug import console_write, errlog_add
from Tasks import exec_lm_pipe
from micropython import mem_info
from machine import freq
try:
    from machine import reset_cause, PWRON_RESET, HARD_RESET, WDT_RESET, DEEPSLEEP_RESET, SOFT_RESET
except ImportError:
    reset_cause = None
try:
    from gc import mem_free
except ImportError:
    from simgc import mem_free

#################################################################
#                          FUNCTIONS                            #
#################################################################


def bootup():
    """
    Executes when system boots up.
    """
    # Execute LMs from boothook config parameter
    console_write("[BOOT] EXECUTION...")
    boot_cause()
    bootasks = cfgget('boothook')
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
    # Autotune queue size
    tune_queue_size()


def tune_queue_size():
    """
    Tune queue size based on available ram
    between 5-50
    """
    min_queue, max_queue, task_req_kb = 5, 20, 20       # 400kb max for tasks management
    est_queue = int(mem_free()/1000/task_req_kb)
    est_queue = max(est_queue, min_queue)
    est_queue = min(est_queue, max_queue)
    current_queue = cfgget('aioqueue')
    if est_queue > current_queue:
        cfgput('aioqueue', est_queue)


def profiling_info(label=""):
    """
    Runtime memory measurements
    """
    if cfgget('dbg'):
        console_write(f"{'~'*5} [PROFILING INFO] - {label} {'~'*5}")
        mem_info()
        console_write("~"*30)


def boot_cause():
    reason = 0, "-Unknown"
    if callable(reset_cause):
        reason = 0, "Unknown"
        reset_reason = reset_cause()
        if reset_reason == PWRON_RESET:
            reason = 1, "PowerOn"
        elif reset_reason == HARD_RESET:
            reason = 2, "HardReset"
        elif reset_reason == WDT_RESET:
            reason = 3, "WDTWakeUp"
        elif reset_reason == DEEPSLEEP_RESET:
            reason = 4, "DSWakeUp"
        elif reset_reason == SOFT_RESET:
            reason = 5, "SoftReset"
    errlog_add(f"[BOOT] info: {reason[1]}")
    return reason
