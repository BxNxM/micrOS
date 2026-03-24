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
from Debug import console_write, syslog
from Tasks import TaskBase, exec_lm_pipe
from Auth import resolve_secret
from machine import freq
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
    # Apply resource tuning before running user boot: queue/performance policy
    boot_cause()            # Load and Save boot cause
    _tune_queue_size()      # Autotune queue size

    # Execute LMs from boothook config parameter
    console_write("[BOOT] EXECUTION...")
    bootasks = cfgget('boothook')
    if bootasks is not None and bootasks.lower() != 'n/a':
        console_write(f"|-[BOOT] TASKS: {bootasks}")
        if exec_lm_pipe(resolve_secret(bootasks)):
            console_write("|-[BOOT] DONE")
        else:
            console_write("|-[BOOT] ERROR")

    # Configure CPU performance
    _tune_performance()


def _tune_queue_size():
    """
    Tune queue size based on available ram
    between 5-50
    """
    min_queue, max_queue, task_req_kb = 5, 20, 20       # 400kb max for tasks management
    est_queue = int(mem_free()/1000/task_req_kb)
    est_queue = max(est_queue, min_queue)
    est_queue = min(est_queue, max_queue)
    current_queue = cfgget('aioqueue')
    # Preserve user tuning, only clamp down when configured queue is too large for current RAM.
    tuned_queue = min(current_queue, est_queue)
    TaskBase.QUEUE_SIZE = tuned_queue
    if tuned_queue != current_queue:
        cfgput('aioqueue', tuned_queue)


def _tune_performance():
    # {(platforms, ...): (min_clock, max_clock), ...}
    cpu_clocks = {
        ('esp32c3', 'esp32c6'): (80_000_000, 160_000_000),
        ('esp32',): (160_000_000, 240_000_000),  # default
    }
    from microIO import detect_platform
    platform = detect_platform()
    cpu_min_max = cpu_clocks[('esp32',)]
    for platforms, clocks in cpu_clocks.items():
        if platform in platforms:
            cpu_min_max = clocks
            break
    # Set boosted (boost mode)
    if cfgget('boostmd'):
        max_hz = cpu_min_max[1]
        console_write(f"[BOOT HOOKS] CPU boost: ON - {max_hz} Hz")
        freq(max_hz)
    else:
        min_hz = cpu_min_max[0]
        console_write(f"[BOOT HOOKS] CPU boost: OFF - {min_hz} Hz")
        freq(min_hz)


def profiling_info(label=""):
    """
    Runtime memory measurements
    """
    if cfgget('dbg'):
        from micropython import mem_info
        console_write(f"{'~'*5} [PROFILING INFO] - {label} {'~'*5}")
        mem_info()
        console_write("~"*30)


def boot_cause():
    reason = 0, "-Unknown"
    try:
        from machine import reset_cause, PWRON_RESET, HARD_RESET, WDT_RESET, DEEPSLEEP_RESET, SOFT_RESET
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
    except ImportError:
        pass
    syslog(f"[BOOT] info: {reason[1]}")
    return reason


def enableESPNow() -> str:
    """
    Enable ESP-NOW communication
    """
    if cfgget('espnow'):
        try:
            from Espnow import ESPNowSS
            verdict = ESPNowSS().start_server()
            console_write(f"[TASK] Start ESPNow-InterCon server: {verdict}")
        except Exception as e:
            syslog(f"[ERR] Start ESPNow-InterCon server: {e}")
            return str(e)
    return "ESPNow disabled"
