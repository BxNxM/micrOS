from time import localtime
from TaskManager import exec_lm_core_schedule
from Debug import console_write, errlog_add
from Time import Sun, suntime, ntp_time

"""
# SYSTEM TIME FORMAT:    Y, M, D, H, M, S, WD, YD
# SCHEDULER TIME FORMAT: WD, H, M, S
WD: 1-7
H: 0-23
M: 0-59
S: 0-59
* - means in every place - every time
"""

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


def __resolve_time_tag(check_time, crontask):
    """
    Handle time stump/tag in check_time
        time stump: (WD, H, M, S)
        tag: sunrise, sunset   <- filter this use case
    """
    # Resolve time tag: sunrise, sunset
    if len(check_time) < 3:
        tag = crontask[0].strip()
        # Resolve tag
        value = Sun.TIME.get(tag, None)
        if value is None or len(value) < 3:
            errlog_add('[cron][ERR] syntax error: {}:{}'.format(tag, value))
            return ()
        # Update check_time with resolved value by tag
        check_time = ('*', value[0], value[1], value[2])
    return check_time


def __scheduler_trigger(cron_time_now, now_sec_tuple, crontask, deltasec=2):
    """
    SchedulerCore logic
        actual time: cron_time_now format: (WD, H, M, S)
        actual time in sec: now_sec_tuple: (H sec, M sec, S)
        crontask: ("WD:H:M:S", "LM FUNC")
        deltasec: sample time window: +/- sec: -sec--|event|--sec-
    """
    # Resolve "normal" time
    check_time = tuple(int(t.strip()) if t.isdigit() else t.strip() for t in crontask[0].split(':'))
    # Resolve "time tag" to "normal" time
    check_time = __resolve_time_tag(check_time, crontask)
    if len(check_time) < 4:
        return False

    # Cron actual time (now) parts summary in sec
    check_time_now_sec = now_sec_tuple[0] + now_sec_tuple[1] + now_sec_tuple[2]
    # Cron overall requested time in sec - hour in sec, minute in sec, sec
    check_time_scheduler_sec = int(now_sec_tuple[0] if check_time[1] == '*' else check_time[1] * 3600) \
                               + int(now_sec_tuple[1] if check_time[2] == '*' else check_time[2] * 60) \
                               + int(now_sec_tuple[2] if check_time[3] == '*' else check_time[3])

    # Time frame +/- corrections
    tolerance_min_sec = 0 if check_time_now_sec - deltasec < 0 else check_time_now_sec - deltasec
    tolerance_max_sec = check_time_now_sec + deltasec

    task_id = "{}:{}|{}".format(check_time[0], check_time_scheduler_sec, str(crontask[1]).replace(' ', ''))

    # Check WD - WEEK DAY
    if check_time[0] == '*' or check_time[0] == cron_time_now[0]:
        # Check H, M, S in sec format between tolerance range
        if tolerance_min_sec <= check_time_scheduler_sec <= tolerance_max_sec:
            __cron_task_cache_manager(check_time_now_sec, deltasec)
            if check_time[3] == '*' or task_id not in LAST_CRON_TASKS:
                lm_state = False
                if isinstance(crontask[1], str):
                    # [1] Execute Load Module as a string (user LMs)
                    lm_state = exec_lm_core_schedule(crontask[1].split())
                else:
                    try:
                        # [2] Execute function reference (built-in functions)
                        console_write("[builtin cron] {}".format(crontask[1]()))
                        lm_state = True
                    except Exception as e:
                        errlog_add("[cron][ERR] function exec error: {}".format(e))
                if not lm_state:
                    console_write("[cron]now[{}]  {} <-> {}  conf[{}] exec[{}] LM: {}".format(cron_time_now,
                                                                                                       __convert_sec_to_time(tolerance_min_sec),
                                                                                                       __convert_sec_to_time(tolerance_max_sec),
                                                                                                       crontask[0],
                                                                                                       lm_state,
                                                                                                       crontask[1]))

                # SAVE TASK TO CACHE
                if check_time[3] != '*':
                    # SAVE WHEN SEC not *
                    LAST_CRON_TASKS.append(task_id)
                return True
    return False


def deserialize_raw_input(raw_cron_input):
    try:
        # Returns (("WD:H:M:S", 'LM FUNC'), ("WD:H:M:S", 'LM FUNC'), ...)
        return tuple(tuple(cron.split('!')) for cron in raw_cron_input.split(';'))
    except Exception as e:
        console_write("[cron] deserialize: syntax error: {}".format(e))
        errlog_add("[cron][ERR] deserialize: syntax error: {}".format(e))
    return tuple()


def scheduler(scheduler_input, irqperiod):
    """
    irqperiod - in sec
    RAW INPUT SYNTAX:
        'WD:H:M:S!CMD;WD:H:M:S!CMD2;...'
    RAW INPUT SYNTAX TAG SUPPORT:
        'sunrise!CMD;sunset!CMD'
    ! - execute
    ; - cron task separator
    """
    builtin_tasks = (("*:3:0:0", suntime), ("*:3:5:0", ntp_time))
    state = False
    time_now = localtime()[0:8]
    # time_now = GEN.__next__()   # TODO: remove after test

    # Actual time - WD, H, M, S
    cron_time_now = (time_now[-2], time_now[-5], time_now[-4], time_now[-3])
    # Cron overall time now in sec - hour in sec, minute in sec, sec
    now_sec_tuple = (cron_time_now[1] * 3600, cron_time_now[2] * 60, cron_time_now[3])

    try:
        # Check builtin tasks (func. ref.)
        for cron in builtin_tasks:
            state |= __scheduler_trigger(cron_time_now, now_sec_tuple, cron, deltasec=irqperiod)
        # Check user tasks (str)
        for cron in deserialize_raw_input(scheduler_input):
            state |= __scheduler_trigger(cron_time_now, now_sec_tuple, cron, deltasec=irqperiod)
        return state
    except Exception as e:
        console_write("[cron] callback error: {}".format(e))
        errlog_add('[cron][ERR] callback error: {}'.format(e))
        return False


'''
if __name__ == '__main__':
    # TEST CODE
    from ConfigHandler import cfgget
    dummyirq_sec(cfgget('crontasks'), int(cfgget('timirqseq')/1000))
'''
