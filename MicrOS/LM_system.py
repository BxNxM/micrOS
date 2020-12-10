from ConfigHandler import progress_led_toggle_adaptor


def info():
    try:
        from gc import mem_free
    except:
        from simgc import mem_free    # simulator mode
    from os import statvfs, getcwd
    from machine import freq
    fs_stat = statvfs(getcwd())
    fs_size = fs_stat[0] * fs_stat[2]
    fs_free = fs_stat[0] * fs_stat[3]
    return {'CPU[Hz]': freq(), 'GC MemFree[byte]': mem_free(), 'FS FREE [%]': int((fs_free/fs_size)*100)}


def gcollect():
    try:
        from gc import collect, mem_free
    except:
        from simgc import collect, mem_free    # simulator mode
    collect()
    return {'GC MemFree[byte]': mem_free()}


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
    cache = {}
    for pds in (_pds for _pds in listdir() if _pds.endswith('.pds')):
        with open(pds, 'r') as f:
            cache[pds] = f.read()
    return cache


def ifmode():
    try:
        with open('.if_mode', 'r') as f:
            return {'if_mode': f.read()}
    except:
        return {'if_mode': 'micros'}


def help():
    return 'info', 'gcollect', 'heartbeat', 'clock', 'ntp', 'module', 'cachedump', 'ifmode'
