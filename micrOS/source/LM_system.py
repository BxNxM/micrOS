from utime import localtime
from Common import socket_stream
from Network import get_mac
from Time import ntptime, settime, suntime, Sun
from Debug import errlog_get, errlog_add, errlog_clean, console_write


@socket_stream
def info(msgobj):
    try:
        from gc import mem_free
    except:
        from simgc import mem_free  # simulator mode
    from os import statvfs, getcwd, uname
    from machine import freq
    fs_stat = statvfs(getcwd())
    fs_size = fs_stat[0] * fs_stat[2]
    fs_free = fs_stat[0] * fs_stat[3]
    mem = mem_free()
    msgobj('CPU clock: {} [MHz]'.format(int(freq() * 0.0000001)))
    msgobj('Free RAM: {} kB {} byte'.format(int(mem / 1024), int(mem % 1024)))
    msgobj('Free fs: {} %'.format(int((fs_free / fs_size) * 100)))
    msgobj('upython: {}'.format(uname()[3]))
    msgobj('board: {}'.format(uname()[4]))
    msgobj('mac: {}'.format(get_mac()))
    return ''


def gclean():
    try:
        from gc import collect, mem_free
    except:
        from simgc import collect, mem_free  # simulator mode
    collect()
    return {'GC MemFree[byte]': mem_free()}


def heartbeat():
    console_write("<3 heartbeat <3")
    return "<3 heartbeat <3"


def clock():
    buff = [str(k) for k in localtime()]
    return "{}  {}\nWD: {} YD: {}".format('.'.join(buff[0:3]), ':'.join(buff[3:6]), buff[6], buff[7])


def ntp():
    """
    Set NTP manually
    """
    from ConfigHandler import cfgget
    try:
        # Automatic setup - over wifi - ntp
        state = ntptime()
        return state, localtime()
    except Exception as e:
        return False, "ntp error:{}".format(e)


def sun(refresh=False):
    if refresh:
        return suntime()
    return Sun.TIME


def setclock(year, month, mday, hour, min, sec):
    """
    Set Localtime + RTC Clock manually
    """
    settime(year, month, mday, hour, min, sec)
    return localtime()


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
    if value > -70:
        return {'VeryGood': value}
    if value > -80:
        return {'Okay': value}
    if value > -90:
        return {'NotGood': value}
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


def pinmap(key='builtin'):
    """
    Get Logical pin by key runtime
    """
    from LogicalPins import physical_pin, get_pinmap
    return {key: physical_pin(key), 'pinmap': get_pinmap()}


def ha_sta():
    """
    Check and repair STA network mode
    """
    from ConfigHandler import cfgget
    from network import STA_IF, WLAN
    # IF NWMD STA AND NOT CONNECTED => REBOOT
    if cfgget('nwmd') == 'STA' and not WLAN(STA_IF).isconnected():
        from machine import reset
        reset()
    return '{} mode, OK'.format(cfgget('nwmd'))


@socket_stream
def alarms(clean=False, test=False, msgobj=None):
    if test:
        errlog_add('TeSt ErRoR')
    if clean:
        errlog_clean()
    errcnt = errlog_get(msgobj=msgobj)
    return {'NOK alarm': errcnt} if errcnt > 0 else {'OK alarm': errcnt}


def ifconfig():
    from Network import ifconfig
    return ifconfig()

#######################
# LM helper functions #
#######################

def help():
    return 'info', 'gclean', 'heartbeat', 'clock',\
           'setclock year month mday hour min sec',\
           'ntp', 'module unload="LM_rgb/None"', \
           'rssi', 'cachedump cdel="rgb.pds/None"', 'lmpacman lm_del="LM_rgb.py/None"',\
           'pinmap key="dhtpin/None"', 'ha_sta', 'alarms clean=False',\
           'sun refresh=False', 'ifconfig'
