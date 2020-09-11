# DUMMY IRQ VALUE
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

LAST_CRON_TASK = ["", ""]

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


def __scheduler_trigger(time_now, scheduler_fragment, sec_tolerance=2):
    """
    SchedulerCore logic
    check format: WD, H, M, S
    """
    check_time = tuple(int(t.strip()) if t.strip() != '*' else t.strip() for t in scheduler_fragment[0].split(':'))
    task_id = "{}{}{}{}{}".format(check_time[0], check_time[1], check_time[2], check_time[3], scheduler_fragment[1].replace(' ', ''))
    check_time_now = (time_now[-2], time_now[-5], time_now[-4], time_now[-3])
    check_time_now_sec = (check_time_now[1] * 3600) + (check_time_now[2] * 60) + check_time_now[3]
    # Time frame +/- corrections
    tolerance_min = __convert_sec_to_time(check_time_now_sec - sec_tolerance)
    tolerance_max = __convert_sec_to_time(check_time_now_sec + sec_tolerance)
    print("{} [{}]\tmin{}<->max{}\tdelta: +/- {}".format(task_id, check_time_now,
                                                              tolerance_min,
                                                              tolerance_max,
                                                              sec_tolerance), end='\r')
    # Check WD - WEEK DAY
    if check_time[0] == '*' or check_time[0] == check_time_now[0]:
        # Check H - HOUR
        if check_time[1] == '*' or tolerance_min[0] <= check_time[1] <= tolerance_max[0]:
            # Check M - MINUTE
            if check_time[2] == '*' or tolerance_min[1] <= check_time[2] <= tolerance_max[1]:
                # Check S - SECOND
                sec_range = range(tolerance_min[2], tolerance_max[2])
                if tolerance_min[2] > tolerance_max[2]:
                    sec_range = tuple(list(range(tolerance_min[2], 60)) + list(range(0, tolerance_max[2])))
                if check_time[3] == '*' or check_time[3] in sec_range:
                    # FILTER TO AVOID REDUNDANT EXECUTION
                    if check_time[3] == '*' or task_id not in LAST_CRON_TASK:
                        lm_state = execute_LM_function_Core(scheduler_fragment[1].split())
                        print("[CRON]NOW[{}]  {} <-> {}  CONF[{}] EXECUTE[{}] LM: {}".format(check_time_now,
                                                                                   tolerance_min,
                                                                                   tolerance_max,
                                                                                   scheduler_fragment[0],
                                                                                   lm_state,
                                                                                   scheduler_fragment[1]))
                        # EXECUTED CACHE
                        if check_time[3] != '*' and check_time[2] != '*':
                            # SAVE WHEN Sec and Min not *
                            LAST_CRON_TASK[1] = task_id
                        elif check_time[2] != '*':
                            # SAVE WHEN Sec not *
                            LAST_CRON_TASK[0] = task_id
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
    # Format: Y, M, D, H, M, S, WD, YD
    #time_now = GEN.__next__()       # TODO: replace with system time
    time_now = localtime()[0:8]
    for cron in scheduler_input:
        state = __scheduler_trigger(time_now, cron, sec_tolerance=irqperiod)
        return_state |= state
    return return_state

