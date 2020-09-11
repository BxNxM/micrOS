# DUMMY IRQ VALUE
IRQSEQ = 1000

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
#     SYSTEM TEST MODULES   #
#############################


def systime(sec):
    h = int(sec / 60 / 60) % 24
    m = int(sec / 60 % 60)
    s = sec % 60
    wd = 1 + int(sec / 60 / 60 / 24) % 7
    day = int(sec/60/60/24) % 30
    return 2020, 9, day, h, m, s, wd, 0


def system_time_generator(max=100000000):
    from random import randint
    generator = (systime(sec) for sec in range(0, max, int(IRQSEQ/1000)+randint(-2, 2)))
    return generator


def dummyirq_sec(raw_cron_input):
    while True:
        scheduler(raw_cron_input)


GEN = system_time_generator()
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
    print("[{}]\tmin{}<->max{}\tdelta: +/- {}".format(check_time_now,
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
                        # TODO: replace with InterpreterCore
                        print("[EXEC]NOW[{}]  {} <-> {}  CONF[{}] EXECUTE LM: {}".format(check_time_now,
                                                                                   tolerance_min,
                                                                                   tolerance_max,
                                                                                   scheduler_fragment[0],
                                                                                   scheduler_fragment[1]))
                        # EXECUTED CACHE
                        if check_time[3] != '*' and check_time[2] != '*':
                            # SAVE WHEN S and M not *
                            LAST_CRON_TASK[1] = task_id
                        elif check_time[2] != '*':
                            # SAVE WHEN S not *
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


def scheduler(raw_cron_input):
    """RAW INPUT SYNTAX:
        '{cron time}!COMD;{cron time2}!COMD2;...'
    ! - execute
    ; - cron task separator
    """
    scheduler_input = deserialize_raw_input(raw_cron_input)
    return_state = False
    # Format: Y, M, D, H, M, S, WD, YD
    time_now = GEN.__next__()       # TODO: replace with system time
    for cron in scheduler_input:
        state = __scheduler_trigger(time_now, cron, sec_tolerance=int(IRQSEQ/1000))
        return_state |= state
    return return_state


if __name__ == "__main__":
    raw_cron_input = '*:10:23:*![0] EVERY SEC;1:10:20:59!\t[1] MONDAY EVENT;\
2:12:25:1!\t[2] TUESDAY EVENT;3:15:30:30!\t[3] WEDNESDAY EVENT;4:18:35:23!\t[4] THURSDAY EVENT;\
5:20:40:56!\t[5] FRIDAY EVENT;6:21:40:0!\t[6] SATURDAY EVENT;7:23:20:0![7] END OF WEEEEEEKKKK;\
*:8:15:0!\t\t[0*1] LAMP ON EVERYDAY;*:10:1:0!\t\t[0*2] LAMP OFF EVERYDAY'

    #scheduler(raw_cron_input)
    dummyirq_sec(raw_cron_input)








