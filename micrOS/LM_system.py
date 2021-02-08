from ConfigHandler import progress_led_toggle_adaptor


def info():
    try:
        from gc import mem_free
    except:
        from simgc import mem_free  # simulator mode
    from os import statvfs, getcwd
    from machine import freq
    from sys import platform
    fs_stat = statvfs(getcwd())
    fs_size = fs_stat[0] * fs_stat[2]
    fs_free = fs_stat[0] * fs_stat[3]
    return {'CPU[Hz]': freq(), 'MemFree[byte]': mem_free(), 'FS FREE [%]': int((fs_free / fs_size) * 100),
            'Plaform': platform}


def gcollect():
    try:
        from gc import collect, mem_free
    except:
        from simgc import collect, mem_free  # simulator mode
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
        (year, month, mday, hour, minute, second, weekday, yearday) = localtime(time() + int(cfgget('gmttime')) * 3600)
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
    if unload in modules.keys():
        del modules[unload]
        return "Module unload {} done.".format(unload)
    return "Module unload {} failed.".format(unload)


def cachedump():
    from os import listdir
    cache = {}
    for pds in (_pds for _pds in listdir() if _pds.endswith('.pds')):
        with open(pds, 'r') as f:
            cache[pds] = f.read()
    return cache


def rssi():
    from network import WLAN, STA_IF
    value = WLAN(STA_IF).status('rssi')
    if value > -67:
        return {'Amazing': value}
    elif value > -70:
        return {'VeryGood': value}
    elif value > -80:
        return {'Okay': value}
    elif value > -90:
        return {'NotGood': value}
    else:
        return {'Unusable': value}


def lmpacman(lm_del=None):
    """
    lm_del: LM_<loadmodulename.py/.mpy>
        Add name without LM_ but with extension
    """
    from os import listdir, remove
    if lm_del is not None and lm_del.endswith('py'):
        # Check LM is in use
        if 'system.' in lm_del:
            return 'Load module {} is in use, skip delete.'.format(lm_del)
        remove('LM_{}'.format(lm_del))
        return 'Delete module: {}'.format(lm_del)
    # Dump available LMs
    return '\n'.join(('   {}'.format(res.replace('LM_', '')) for res in listdir() if 'LM_' in res))


def getpin(key='builtin'):
    from sys import modules
    from LogicalPins import get_pin_on_platform_by_key
    return {key: get_pin_on_platform_by_key(key), 'pinmap':
        ', '.join((mdl.replace('LP_', '').split('.')[0] for mdl in modules.keys() if mdl.startswith('LP_')))}


def help():
    return 'info', 'gcollect', 'heartbeat', 'clock', 'ntp', 'module',\
           'rssi', 'cachedump', 'lmpacman', 'getpin'
