from time import localtime
from InterpreterCore import execute_LM_function_Core

'''
# SYSTEM TIME FORMAT:    Y, M, D, H, M, S, WD, YD
# SCHEDULER TIME FORMAT: WD, H, M, S
WD: 1-7
H: 0-23
M: 0-59
S: 0-59
* - means in every place - every time
'''

LAST_CRON_TASKS = []

'''
#############################
#     SYSTEM TEST MODULES   #
#############################


def systime(sec):
    h = int(sec / 60 / 60) % 24
    m = int(sec / 60 % 60)
    s = sec % 60
    wd = int(sec / 60 / 60 / 24) % 7
    day = int(sec / 60 / 60 / 24) % 30
    return 2020, 9, day, h, m, s, wd, 0


def system_time_generator(max=100000000):
    generator = (systime(sec) for sec in range(0, max, 3))
    return generator


def dummyirq_sec(raw_cron_input, irqperiod):
    from time import sleep
    while True:
        scheduler(raw_cron_input, irqperiod)
        sleep(0.00001)


GEN = system_time_generator()
'''


#############################
#    SCHEDULER FUNCTIONS    #
#############################


def __convert_sec_to_time(seconds):
    """Convert sec to time format"""
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return hour, minutes, seconds


def __cron_task_cache_manager(now_in_sec, sec_tolerant):
    """
    Cron tasks execution cache by task id
        - to avoid unwanted re-executions
    """
    # Iterate on already executed tasks cache
    for index, taskid in enumerate(LAST_CRON_TASKS):
        # Get H,M,S in sec from task id
        tasktime_in_sec = int(str(taskid.split('|')[0]).split(':')[1])
        sec_diff = tasktime_in_sec - (now_in_sec - sec_tolerant)
        # Remove outdated cache registration
        if sec_diff < 0 or sec_diff > 20:
            LAST_CRON_TASKS.remove(LAST_CRON_TASKS[index])


def __scheduler_trigger(cron_time_now, check_time_now_sec_tuple, scheduler_fragment, sec_tolerance=2):
    """
    SchedulerCore logic
        cron time now format: WD, H, M, S
    """
    check_time = tuple(int(t.strip()) if t.strip() != '*' else t.strip() for t in scheduler_fragment[0].split(':'))
    # Cron actual time (now) parts summary in sec
    check_time_now_sec = check_time_now_sec_tuple[0] + check_time_now_sec_tuple[1] + check_time_now_sec_tuple[2]
    # Cron overall requested time in sec - hour in sec, minute in sec, sec
    check_time_scheduler_sec = int(check_time_now_sec_tuple[0] if check_time[1] == '*' else check_time[1] * 3600) \
                               + int(check_time_now_sec_tuple[1] if check_time[2] == '*' else check_time[2] * 60) \
                               + int(check_time_now_sec_tuple[2] if check_time[3] == '*' else check_time[3])

    # Time frame +/- corrections
    tolerance_min_sec = 0 if check_time_now_sec - sec_tolerance < 0 else check_time_now_sec - sec_tolerance
    tolerance_max_sec = check_time_now_sec + sec_tolerance

    task_id = "{}:{}|{}".format(check_time[0], check_time_scheduler_sec, scheduler_fragment[1].replace(' ', ''))

    # Check WD - WEEK DAY
    if check_time[0] == '*' or check_time[0] == cron_time_now[0]:
        # Check H, M, S in sec format between tolerance range
        if tolerance_min_sec <= check_time_scheduler_sec <= tolerance_max_sec:
            __cron_task_cache_manager(check_time_now_sec, sec_tolerance)
            if check_time[3] == '*' or task_id not in LAST_CRON_TASKS:
                lm_state = execute_LM_function_Core(scheduler_fragment[1].split())
                if not lm_state:
                    print("[CRON ERROR]NOW[{}]  {} <-> {}  CONF[{}] EXECUTE[{}] LM: {}".format(cron_time_now,
                                                                                               __convert_sec_to_time(tolerance_min_sec),
                                                                                               __convert_sec_to_time(tolerance_max_sec),
                                                                                               scheduler_fragment[0],
                                                                                               lm_state,
                                                                                               scheduler_fragment[1]))

                # SAVE TASK TO CACHE
                if check_time[3] != '*':
                    # SAVE WHEN SEC not *
                    LAST_CRON_TASKS.append(task_id)
                return True
    return False


def deserialize_raw_input(raw_cron_input):
    datastruct = []
    try:
        datastruct = [tuple(cron.split('!')) for cron in raw_cron_input.split(';')]
    except Exception as e:
        print("deserialize_raw_input: input syntax error: {}".format(e))
    return datastruct


def scheduler(raw_cron_input, irqperiod):
    """
    irqperiod - in sec
    RAW INPUT SYNTAX:
        '{cron time}!COMD;{cron time2}!COMD2;...'
    ! - execute
    ; - cron task separator
    """
    scheduler_input = deserialize_raw_input(raw_cron_input)
    return_state = False
    time_now = localtime()[0:8]
    # time_now = GEN.__next__()   # TODO: remove after test

    # Actual time - WD, H, M, S
    cron_time_now = (time_now[-2], time_now[-5], time_now[-4], time_now[-3])
    # Cron overall time now in sec - hour in sec, minute in sec, sec
    check_time_now_sec_tuple = (cron_time_now[1] * 3600, cron_time_now[2] * 60, cron_time_now[3])

    for cron in scheduler_input:
        state = __scheduler_trigger(cron_time_now, check_time_now_sec_tuple, cron, sec_tolerance=irqperiod)
        return_state |= state
    return return_state


'''
if __name__ == '__main__':
    # TEST CODE
    from ConfigHandler import cfgget
    dummyirq_sec(cfgget('crontasks'), int(cfgget('timirqseq')/1000))
'''
