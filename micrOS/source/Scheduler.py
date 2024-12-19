from time import localtime
from re import compile
from Tasks import exec_lm_pipe_schedule
from Debug import console_write, errlog_add
from Time import Sun, suntime, ntp_time

"""
# SYSTEM TIME FORMAT:    Y, M, D, H, M, S, WD, YD
# SCHEDULER TIME FORMAT: WD, H, M, S
WD: 0-6
H:  0-23
M:  0-59
S:  0-59
* - means in every place - every time
"""

LAST_CRON_TASKS = []

'''
#############################
#     SYSTEM TEST MODULES   #
#############################

def system_time_generator(max=100000000):

    def systime(sec):
        h = int(sec / 60 / 60) % 24
        m = int(sec / 60 % 60)
        s = sec % 60
        wd = int(sec / 60 / 60 / 24) % 7
        day = int(sec / 60 / 60 / 24) % 30
        return 2020, 9, day, h, m, s, wd, 0
    
    generator = (systime(sec) for sec in range(0, max, 3))
    return generator

def dummy_irq(cron_data, irqperiod):
    from time import sleep
    while True:
        scheduler(cron_data, irqperiod)
        sleep(0.00001)

##### TEST CODE INIT #####
# Create time gen (use instead localtime)
GEN = system_time_generator()
from ConfigHandler import cfgget
# Emulate scheduler execution ... LOOP
dummy_irq(cfgget('crontasks'), int(cfgget('timirqseq')/1000))
'''


#############################
#    SCHEDULER FUNCTIONS    #
#############################


def __convert_sec_to_time(seconds):
    """Convert sec to time format"""
    seconds = seconds % 86400           # (24 * 3600) -> 24h in seconds
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
    Handle time stamp/tag in check_time
        time stamp: (WD, H, M, S)
        tag: sunrise, sunset   <-- handled by this function
        tag: sunrise+-min, sunset+-min   <-- handled by this function
    """
    # Resolve time tag: sunrise, sunset
    if len(check_time) < 3:
        tag = crontask[0].strip()

        # Handle tag offset
        offset = 0  # minute offset from suntime+-min
        tag_regex = compile(r"(\w+)([+|-]\d+)")
        match_obj = tag_regex.search(tag)
        if match_obj:
            tag = match_obj.group(1)
            offset = int(match_obj.group(2))

        # Resolve tag
        value = Sun.TIME.get(tag, None)
        if value is None or len(value) < 3:
            errlog_add(f'[ERR] cron syntax error: {tag}:{value}')
            return ()

        # Update check_time with resolved value by tag
        if offset:
            offset_time = (value[0]*60 + value[1]) + offset
            offset_time = offset_time if offset_time > 0 else 1440 + offset_time        # 1440 -> 24h in minutes
            h, m, _ = __convert_sec_to_time(offset_time * 60)
            check_time = ('*', h, m, value[2])
            return check_time
        check_time = ('*', value[0], value[1], value[2])
    return check_time


def __check_wd(wd, wd_now):
    """
    Check weekday param
    :param wd: could be given in 3 syntax
        *           -> select all day 0 ... 6
        0 ... 6     -> exact value, 0=Monday - 6=Sunday
        {from}-{to} -> range, example: 0-3 means Monday to Wednesday
    :param wd_now: actual (now) workday
    """
    # Handle WD range syntax
    wd_regex = compile(r"(\d+)-(\d+)")
    match_obj = wd_regex.search(wd)
    if match_obj:
        wd_from = int(match_obj.group(1))
        wd_to = int(match_obj.group(2))
        # Check incremental range: 4-6
        if wd_from < wd_to and wd_now in range(wd_from, wd_to+1):
            return True
        # Check decremental range: 5-1
        if wd_from > wd_to and wd_now in list(range(wd_from, 7)) + list(range(0, wd_to+1)):
            return True
    # Handle WD * and exact values
    return wd in ('*', wd_now)


def __scheduler_trigger(cron_time_now, crontask, deltasec=2):
    """
    SchedulerCore logic
        actual time: cron_time_now format: (WD, H, M, S)
        actual time in sec: now_sec_tuple: (H sec, M sec, S)
        crontask: ("WD:H:M:S", "LM FUNC") or ("time tag", "LM FUNC")
        deltasec: sample time window: +/- sec: -sec--|event|--sec-
    """
    # Resolve "normal" time
    check_time = tuple(int(t.strip()) if t.isdigit() else t.strip() for t in crontask[0].split(':'))
    # Resolve "time tag" to "normal" time
    check_time = __resolve_time_tag(check_time, crontask)
    if len(check_time) < 4:
        return False

    # Cron overall time now in sec - hour in sec, minute in sec, sec
    now_sec_tuple = (cron_time_now[1] * 3600, cron_time_now[2] * 60, cron_time_now[3])
    # Cron actual time (now) parts summary in sec
    check_time_now_sec = now_sec_tuple[0] + now_sec_tuple[1] + now_sec_tuple[2]
    # Cron overall requested time in sec - hour in sec, minute in sec, sec
    check_time_scheduler_sec = int(now_sec_tuple[0] if check_time[1] == '*' else check_time[1] * 3600) \
                               + int(now_sec_tuple[1] if check_time[2] == '*' else check_time[2] * 60) \
                               + int(now_sec_tuple[2] if check_time[3] == '*' else check_time[3])

    # Time frame +/- corrections
    tolerance_min_sec = 0 if check_time_now_sec - deltasec < 0 else check_time_now_sec - deltasec
    tolerance_max_sec = check_time_now_sec + deltasec

    task_id = f"{check_time[0]}:{check_time_scheduler_sec}|{str(crontask[1]).replace(' ', '')}"

    # Check WD - WEEK DAY
    if __check_wd(wd=check_time[0], wd_now=cron_time_now[0]):
        # Check H, M, S in sec format between tolerance range
        if tolerance_min_sec <= check_time_scheduler_sec <= tolerance_max_sec:
            __cron_task_cache_manager(check_time_now_sec, deltasec)
            if check_time[3] == '*' or task_id not in LAST_CRON_TASKS:
                lm_state = False
                if isinstance(crontask[1], str):
                    # [1] Execute Load Module as a string (user LMs)
                    lm_state = exec_lm_pipe_schedule(crontask[1])
                else:
                    try:
                        # [2] Execute function reference (built-in functions)
                        console_write(f"[builtin cron] {crontask[1]()}")
                        lm_state = True
                    except Exception as e:
                        errlog_add(f"[ERR] cron function exec error: {e}")
                if not lm_state:
                    console_write(f"[cron]now[{cron_time_now}]  \
                        {__convert_sec_to_time(tolerance_min_sec)} <-> {__convert_sec_to_time(tolerance_max_sec)}  \
                        conf[{crontask[0]}] \
                        exec[{lm_state}] \
                        LM: {crontask[1]}")

                # SAVE TASK TO CACHE
                if check_time[3] != '*':
                    # SAVE WHEN SEC not *
                    LAST_CRON_TASKS.append(task_id)
                return True
    return False


def deserialize_raw_input(cron_data):
    """
    Scheduler/Cron input string format
    :param cron_data: raw cron tasks, time based task execution input (bytearray)
        example: WD:H:M:S!LM func;WD:H:M:S!LM func; ...
        multi command example: WD:H:M:S!LM func;LM func2;; WD:H:M:S!LM func;; ...

        time_tag: timestamp / time-tag aka suntime
                timestamp: WD:H:M:S
                    WD: 0...6, 0=Monday, 6=Sunday
                        optional range handling: 0-2 means Monday to Wednesday
                time-tag: sunrise, sunset
                    optional minute offset (+/-): sunrise+30
        task: LoadModule function args
    Returns tuple: (("WD:H:M:S", 'LM FUNC'), ("WD:H:M:S", 'LM FUNC'), ...)
    """
    try:
        # Parse and create return
        cd = str(cron_data, 'utf-8')            # convert cron_data (bytearray) to string
        sep = ';;' if ';;' in cd else ';'       # support multi command with ;;
        return (tuple(cron.split('!')) for cron in cd.split(sep))
    except Exception as e:
        errlog_add(f"[ERR] cron deserialize - syntax error: {e}")
    return ()


def scheduler(cron_data, irqperiod):
    """
    :param cron_data: bytearray data (check syntax down below)
    :param irqperiod: - in sec
    RAW INPUT SYNTAX:
        'WD:H:M:S!CMD;WD:H:M:S!CMD2;...'
    RAW INPUT SYNTAX TAG SUPPORT:
        'sunrise!CMD;sunset!CMD'
    ! - execute
    ; - cron task separator
    """
    builtin_tasks = (("*:3:0:0", suntime), ("*:3:5:0", ntp_time))
    state = False
    time_now = localtime()[3:7]
    # time_now = next(GEN)         # USE FOR TESTING (time machine)

    # Actual time - WD, H, M, S
    cron_time_now = (time_now[3], time_now[0], time_now[1], time_now[2])

    try:
        # Check builtin tasks (func. ref.)
        for cron in builtin_tasks:
            state |= __scheduler_trigger(cron_time_now, cron, deltasec=irqperiod)
        # Check user tasks (str)
        for cron in deserialize_raw_input(cron_data):
            state |= __scheduler_trigger(cron_time_now, cron, deltasec=irqperiod)
        return state
    except Exception as e:
        errlog_add(f'[ERR] cron callback error: {e}')
        return False
