from ConfigHandler import progress_led_toggle_adaptor


def memfree():
    from gc import mem_free
    from machine import freq
    return "CPU[Hz]: {}\nGC MemFree[byte]: {}".format(freq(), mem_free())


def gcollect():
    from gc import collect, mem_free
    collect()
    return "GC MemFree[byte]: {}".format(mem_free())


@progress_led_toggle_adaptor
def heartbeat():
    from time import sleep
    sleep(0.1)
    return "<3 heartbeat <3"


def clock():
    from time import localtime
    return localtime()


def ntp():
    try:
        from time import localtime, time
        from ntptime import settime
        from machine import RTC
        from ConfigHandler import cfgget

        # Sync with NTP server
        settime()
        # Get localtime + GMT
        (year, month, mday, hour, minute, second, weekday, yearday) = localtime(time() + int(cfgget('gmttime'))*3600)
        # Create RealTimeClock + Set RTC with time (+timezone)
        RTC().datetime((year, month, mday, 0, hour, minute, second, 0))
        # Print time
        return localtime()
    except Exception as e:
        return "NTP time errer.:{}".format(e)


def module(unload=None):
    from sys import modules
    if unload is None:
        return modules.keys()
    try:
        del modules[unload]
        return "Module unload {} done.".format(unload)
    except Exception as e:
        return "Module unload failed: {}".format(e)


def cachedump():
    from os import listdir
    return_str = ""
    for pds in (_pds for _pds in listdir() if _pds.endswith('.pds')):
        return_str += "{}: ".format(pds)
        with open(pds, 'r') as f:
            return_str += "{}\n".format(f.read())
    return return_str


def scheduler(cron='*:*:*:*', lm='system', fg='heartbeat', period=2):
    task = '{}!{} {}'.format(cron, lm, fg)
    from Scheduler import scheduler
    return scheduler(task, period)


def help():
    return 'memfree', 'gcollect', 'heartbeat', 'clock', 'ntp', 'module', 'cachedump',\
           'scheduler(cron, lm, fg, irqperiod)'
