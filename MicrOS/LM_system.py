from ConfigHandler import progress_led_toggle_adaptor

def memfree():
    from gc import mem_free
    from machine import freq
    return "CPU[Hz]: {}\nGC MemFree[byte]: {}".format(freq(), mem_free())


def gccollect():
    from gc import collect, mem_free
    collect()
    return "GC MemFree[byte]: {}".format(mem_free())


@progress_led_toggle_adaptor
def heartbeat():
    from time import sleep
    sleep(0.1)
    return "<3 heartbeat <3"


def time():
    from time import localtime
    return localtime()


def setNTP():
    from Network import setNTP_RTC
    if setNTP_RTC():
        return time()
    else:
        return "NTP-RTC setup failed."


def modules(unload=None):
    from sys import modules
    if unload is None:
        return modules.keys()
    else:
        try:
            del modules[unload]
            return "Module unload {} done.".format(unload)
        except Exception as e:
            return "Module unload failed: {}".format(e)


def help():
    return ('memfree', 'gccollect', 'heartbeat', 'time', 'modules')
