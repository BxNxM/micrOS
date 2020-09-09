from time import sleep
IRQSEQ = 2000

# SYSTEM TIME FORMAT:    Y, M, D, H, M, S, WD, YD
# SCHEDULER TIME FORMAT: WD, H, M, S
# 1:18:2:1
# *:*:*:*
scheduler_input = [('1:18:20:5', "[1]MONDAY EVENT"),
                   ('3:20:1:5', "[2]WEDNESDAY EVENT"),
                   ('*:8:15:5', "[3]LAMP ON EVERYDAY"),
                   ('*:10:1:5', "[4]LAMP OFF EVERYDAY"),
                   ('5:20:0:*', "[5]EVERY SEC ON FRIDAY"),
                   ('7:23:20:15', "[6]END OF WEEEEEEKKKK")]

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
    generator = (systime(sec) for sec in range(0, max, int(IRQSEQ/1000)))
    return generator


def dummyirq_sec():
    while True:
        scheduler()


GEN = system_time_generator()
#############################
#    SCHEDULER FUNCTIONS    #
#############################


def __convert_sec_to_time(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return hour, minutes, seconds


def __scheduler_trigger(scheduler_fragment, sec_tolerance=2):
    sec_tolerance *= 2
    # Format: WD, H, M, S
    check_time = tuple(int(t.strip()) if t.strip() != '*' else t.strip() for t in scheduler_fragment[0].split(':'))
    # Format: Y, M, D, H, M, S, WD, YD
    time_now = GEN.__next__()       # TODO: replace with system time
    check_time_now = (time_now[-2], time_now[-5], time_now[-4], time_now[-3])
    check_time_now_sec = (check_time_now[1] * 3600) + (check_time_now[2] * 60) + check_time_now[3]
    # Time frame +/- corrections
    tolerance_min = __convert_sec_to_time(check_time_now_sec - sec_tolerance)
    tolerance_max = __convert_sec_to_time(check_time_now_sec + sec_tolerance)
    #print("[{}]\tmin{}<->max{}\tdelta: +/- {}".format(check_time_now,
    #                                                  tolerance_min,
    #                                                  tolerance_max,
    #                                                  sec_tolerance), end='\r')
    sleep(0.0001) # TODO: REMOVE
    # Check WD - WEEK DAY
    if check_time[0] == '*' or check_time[0] == check_time_now[0]:
        # Check H - HOUR
        if check_time[1] == '*' or tolerance_min[0] <= check_time[1] <= tolerance_max[0]:
            # Check M - MINUTE
            if check_time[2] == '*' or tolerance_min[1] <= check_time[2] <= tolerance_max[1]:
                # Check S - SECOND
                min, max = tolerance_min[2], tolerance_max[2]
                if tolerance_min[2] > tolerance_max[2]:
                    min, max = tolerance_max[2], tolerance_min[2]
                if check_time[3] == '*' or min <= check_time[3] <= max:
                    # Execute load module TODO
                    print("[EXEC][{}] {} <-> {} [{}] EXECUTE LM: {}".format(check_time_now,
                                                                   tolerance_min,
                                                                   tolerance_max,
                                                                   scheduler_fragment[0],
                                                                   scheduler_fragment[1]))
                """
                else:
                    print("[SKIP EXEC][{} -- {}] EXECUTE LM: {} [{}-{}]".format(check_time_now,
                                                                   scheduler_fragment[0],
                                                                   scheduler_fragment[1],
                                                                   tolerance_min,
                                                                   tolerance_max))
                """



def scheduler():
    for cron in scheduler_input:
        #__scheduler_trigger(cron)
        __scheduler_trigger(cron, sec_tolerance=int(IRQSEQ/1000))
        

if __name__ == "__main__":
    #scheduler()
    dummyirq_sec()








