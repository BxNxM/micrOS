from time import sleep
IRQSEQ = 1000

# SYSTEM TIME FORMAT:    Y, M, D, H, M, S, WD, YD
# SCHEDULER TIME FORMAT: WD, H, M, S
# 1:18:2:1
# *:*:*:*
scheduler_input = [('1:18:20:5', "MONDAY 18:20 EVENT"),
                   ('3:20:1:5', "WEDNESDAY 20:1 EVENT"),
                   ('*:8:15:5', "LAMP ON EVERYDAY"),
                   ('*:10:0:5', "LAMP OFF EVERYDAY"),
                   ('5:20:0:*', "EVERY SEC ON FRIDAY 20:0")]

#############################
#     SYSTEM TEST MODULES   #
#############################


def systime(sec):
    h = int(sec / 60 / 60) % 24
    m = int(sec / 60 % 60)
    s = sec % 60
    wd = int(sec / 60 / 60 / 24) % 7
    day = int(sec/60/60/24) % 30
    return 2020, 9, day, h, m, s, wd, 0


def system_time_generator(max=100000000):
    generator = (systime(sec) for sec in range(0, max, int(IRQSEQ/1000)))
    return generator


def dummyirq_sec():
    while True:
        scheduler()


GEN = system_time_generator()
#############################
#    SCHEDULER FUNCTIONS    #
#############################


def __scheduler_trigger(scheduler_fragment, sec_tolerance=2):
    # Format: WD, H, M, S
    check_time = tuple(int(t.strip()) if t.strip() != '*' else t.strip() for t in scheduler_fragment[0].split(':'))
    # Format: Y, M, D, H, M, S, WD, YD
    time_now = GEN.__next__()       # TODO: replace with system time
    check_time_now = (time_now[-2], time_now[-5], time_now[-4], time_now[-3])
    # (Mmin, Smin), (Mmax, Smax) time frame correction
    tolerance_max_m_s = (int(((check_time_now[-2] * 60 + check_time_now[-1]) + sec_tolerance) / 60), int(check_time_now[-1] + sec_tolerance) % 60)
    tolerance_min_m_s = (int(((check_time_now[-2] * 60 + check_time_now[-1]) - sec_tolerance) / 60), int(check_time_now[-1] - sec_tolerance) % 60)
    #print("|{}<->{}|{}|\n".format(tolerance_min_m_s, tolerance_max_m_s, check_time_now))
    print(time_now, end='\r')               # TODO: remove
    sleep(0.0001)                           # TODO: REMOVE
    # Check WD - WEEK DAY
    if check_time[0] == '*' or check_time[0] == check_time_now[0]:
        # Check H - HOUR
        if check_time[1] == '*' or check_time[1] == check_time_now[1]:
            # Check M - MINUTE
            if check_time[2] == '*' or tolerance_min_m_s[0] <= check_time[2] <= tolerance_max_m_s[0]:
                # Check S - SECOND
                if check_time[3] == '*' or tolerance_min_m_s[1] <= check_time[3] <= tolerance_max_m_s[1]:
                    # Execute load module TODO
                    print("[EXEC][{} -- {}] EXECUTE LM: {}".format(check_time_now,
                                                                   scheduler_fragment[0],
                                                                   scheduler_fragment[1]))


def scheduler():
    for cron in scheduler_input:
        __scheduler_trigger(cron)


if __name__ == "__main__":
    #scheduler()
    dummyirq_sec()








