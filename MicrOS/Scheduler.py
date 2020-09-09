from time import sleep
from random import randint
IRQSEQ = 2000

# SYSTEM TIME FORMAT:    Y, M, D, H, M, S, WD, YD
# SCHEDULER TIME FORMAT: WD, H, M, S
# 1:18:2:1
# *:*:*:*
scheduler_input = [('1:10:20:0', "[1] MONDAY EVENT"),
                   ('2:12:25:0', "[2] TUESDAY EVENT"),
                   ('3:15:30:0', "[3] WEDNESDAY EVENT"),
                   ('4:18:35:0', "[4] THURSDAY EVENT"),
                   ('5:20:40:0', "[5] FRIDAY EVENT"),
                   ('6:21:40:0', "[6] SATURDAY EVENT"),
                   ('7:23:20:0', "[7] END OF WEEEEEEKKKK"),
                   ('*:8:15:0', "[0*1] LAMP ON EVERYDAY"),
                   ('*:10:1:0', "[0*2] LAMP OFF EVERYDAY")]
LAST_CRON_TASK = ["", 1, 1]

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
    generator = (systime(sec) for sec in range(0, max, int(IRQSEQ/1000)+randint(-2, 2)))
    return generator


def dummyirq_sec():
    while True:
        scheduler()


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


def dimensioning_metica():
    """Dump dimensioning data for timing feedback"""
    print("------ [STAT] {} relevant/all triggers: {}% [{}][{}]".format(LAST_CRON_TASK[0],
                                                                        int((LAST_CRON_TASK[1] / (
                                                                             LAST_CRON_TASK[2] + LAST_CRON_TASK[
                                                                             1])) * 100),
                                                                        LAST_CRON_TASK[1],
                                                                        LAST_CRON_TASK[2]))


def dimensioning():
    """Cron controller feedback value - for runtime sample time control"""
    if LAST_CRON_TASK[1] >= 20 or LAST_CRON_TASK[2] >= 20:
        normalize = LAST_CRON_TASK[1] if LAST_CRON_TASK[1] < LAST_CRON_TASK[2] else LAST_CRON_TASK[2]
        LAST_CRON_TASK[1] -= normalize
        LAST_CRON_TASK[2] -= normalize
    return 10 * (1 - LAST_CRON_TASK[1] / (LAST_CRON_TASK[2] + LAST_CRON_TASK[1]))


def __scheduler_trigger(scheduler_fragment, sec_tolerance=2):
    """
    SchedulerCore logic
    """
    sec_tolerance += int(dimensioning() * sec_tolerance)  # time edge correction
    # Format: WD, H, M, S
    check_time = tuple(int(t.strip()) if t.strip() != '*' else t.strip() for t in scheduler_fragment[0].split(':'))
    task_id = "{}{}{}{}{}".format(check_time[0], check_time[1], check_time[2], check_time[3], scheduler_fragment[1].replace(' ', ''))
    # Format: Y, M, D, H, M, S, WD, YD
    time_now = GEN.__next__()       # TODO: replace with system time
    check_time_now = (time_now[-2], time_now[-5], time_now[-4], time_now[-3])
    check_time_now_sec = (check_time_now[1] * 3600) + (check_time_now[2] * 60) + check_time_now[3]
    # Time frame +/- corrections
    tolerance_min = __convert_sec_to_time(check_time_now_sec - sec_tolerance)
    tolerance_max = __convert_sec_to_time(check_time_now_sec + sec_tolerance)
    print("[{}]\tmin{}<->max{}\tdelta: +/- {}".format(check_time_now,
                                                      tolerance_min,
                                                      tolerance_max,
                                                      sec_tolerance), end='\r')
    sleep(0.0001) # TODO: REMOVE
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
                    # In timerange call metric (sample)
                    LAST_CRON_TASK[1] += 1
                    # FILTER TO AVOID REDUNDANT EXECUTION
                    if check_time[3] == '*' or task_id not in LAST_CRON_TASK[0]:
                        # Execute load module TODO
                        print("[EXEC]NOW[{}]  {} <-> {}  CONF[{}] EXECUTE LM: {}".format(check_time_now,
                                                                                   tolerance_min,
                                                                                   tolerance_max,
                                                                                   scheduler_fragment[0],
                                                                                   scheduler_fragment[1]))
                        # Store last executed task_id
                        LAST_CRON_TASK[0] = task_id
                        dimensioning_metica()
                else:
                    # Out timerange call metric (sample)
                    LAST_CRON_TASK[2] += 1
                    """
                    print("----------[SKIPEXEC]NOW[{}]  {} <-> {}  CONF[{}] EXECUTE LM: {}".format(check_time_now,
                                                                                   tolerance_min,
                                                                                   tolerance_max,
                                                                                   scheduler_fragment[0],
                                                                                   scheduler_fragment[1]))
                    """


def scheduler():
    for cron in scheduler_input:
        #__scheduler_trigger(cron)
        __scheduler_trigger(cron, sec_tolerance=int(IRQSEQ/1000))


if __name__ == "__main__":
    #scheduler()
    dummyirq_sec()








