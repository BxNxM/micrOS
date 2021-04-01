from ConfigHandler import progress_led_toggle_adaptor
from Common import socket_stream


@socket_stream
def info(msgobj):
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
    mem = mem_free()
    msgobj('CPU clock: {} [MHz]'.format(int(freq() * 0.0000001)))
    msgobj('MemFree: {} kB {} byte'.format(int(mem / 1024), int(mem % 1024)))
    msgobj('FSFREE: {} %'.format(int((fs_free / fs_size) * 100)))
    msgobj('Plaform: {}'.format(platform))
    return ''


def gclean():
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
    """
    Set NTP manually
    """
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
    """
    List and unload LM modules
    """
    from sys import modules
    if unload is None:
        return list(modules.keys())
    if unload in modules.keys():
        del modules[unload]
        return "Module unload {} done.".format(unload)
    return "Module unload {} failed.".format(unload)


@socket_stream
def cachedump(cdel=None, msgobj=None):
    """
    Cache system persistent data storage files (.pds)
    """
    if cdel is None:
        # List pds files aka application cache
        from os import listdir
        for pds in (_pds for _pds in listdir() if _pds.endswith('.pds')):
            with open(pds, 'r') as f:
                msgobj('{}: {}'.format(pds, f.read()))
        return ''
    # Remove given pds file
    from os import remove
    try:
        remove('{}.pds'.format(cdel))
        return '{}.pds delete done.'.format(cdel)
    except:
        return '{}.pds not exists'.format(cdel)


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


@socket_stream
def lmpacman(lm_del=None, msgobj=None):
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
    for k in (res.replace('LM_', '') for res in listdir() if 'LM_' in res):
        msgobj('   {}'.format(k))
    return ''


def getpin(key='builtin'):
    """
    Get Logical pin by key runtime
    """
    from sys import modules
    from LogicalPins import get_pin_on_platform_by_key
    return {key: get_pin_on_platform_by_key(key), 'pinmap':
        ', '.join((mdl.replace('LP_', '').split('.')[0] for mdl in modules.keys() if mdl.startswith('LP_')))}


def ha_sta():
    """
    Check and repair STA network mode
    """
    from ConfigHandler import cfgget
    if cfgget('nwmd') == 'STA':
        from network import STA_IF, WLAN
        # Set STA and Connect
        if not WLAN(STA_IF).isconnected():
            # Soft reset micropython VM - fast recovery
            from machine import soft_reset
            soft_reset()
    return '{} mode, OK'.format(cfgget('nwmd'))


def help():
    return 'info', 'gclean', 'heartbeat', 'clock', 'ntp', 'module unload=<LM_.py/.mpy>', \
           'rssi', 'cachedump cdel=<pds name>', 'lmpacman lm_del=<LM_>', 'getpin', 'ha_sta'
