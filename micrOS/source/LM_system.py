from os import statvfs, getcwd
from utime import localtime
from Common import socket_stream
from Network import get_mac
from Time import ntp_time, set_time, uptime
from Tasks import Manager

try:
    from gc import mem_free, mem_alloc, collect
except:
    from simgc import mem_free, mem_alloc, collect  # simulator mode


def memory_usage():
    """
    Calculate used micropython memory (ram)
    return: memory usage %, memory usage in bytes
    """
    collect()
    total_memory = mem_free() + mem_alloc()
    used_memory = mem_alloc()
    used_mem_percent = round(used_memory / total_memory * 100, 1)
    return {'percent': used_mem_percent, 'mem_used': used_memory}


def disk_usage():
    """
    Calculate used disk space
    return: memory usage %, disk usage in bytes
    """
    fs_stat = statvfs(getcwd())
    fs_size = fs_stat[0] * fs_stat[2]
    fs_free = fs_stat[0] * fs_stat[3]
    used_space = fs_size - fs_free
    used_fs_percent = round(used_space / fs_size * 100, 1)
    return {'percent': used_fs_percent, 'fs_used': used_space}


def top():
    """
    Mini system monitor (top)
    """
    return {'Mem usage [%]': memory_usage()['percent'],
            'FS usage [%]': disk_usage()['percent'],
            'CPU load [%]': Manager.LOAD}


def info():
    """
    Show system info message
    - cpu clock, ram, free fs, upython, board, mac addr, uptime
    """
    from machine import freq
    from os import uname

    buffer = top()
    buffer.update({'CPU clock [MHz]': int(freq() * 0.0000001), 'upython': uname()[3],
              'board': uname()[4], 'uptime': uptime()})
    try:
        buffer['mac'] = get_mac()
    except:
        buffer['mac'] = 'n/a'
    return buffer


def gclean():
    """
    Run micropython garbage collection
    """
    try:
        from gc import collect, mem_free
    except:
        from simgc import collect, mem_free  # simulator mode
    collect()
    return {'GC MemFree[byte]': mem_free()}


def heartbeat():
    """
    Test function for built-in led blinking and test reply message
    """
    return "<3 heartbeat <3"


def clock():
    """
    Get formatted localtime value
    Format:
        YYYY.MM.DD  hh:mm:ss
        WD: 0-6 YD: 0-364
    """
    buff = [str(k) for k in localtime()]
    date, time = '.'.join(buff[0:3]), ':'.join(buff[3:6])
    return f"{date}  {time}\nWD: {buff[6]} YD: {buff[7]}"


def ntp():
    """
    Trigger NTP time sync
    """
    try:
        # Automatic setup - over wifi - ntp
        state = ntp_time()
        return state, localtime()
    except Exception as e:
        return False, f"ntp error:{e}"


def sun(refresh=False):
    """
    Get sunset/sunrise time stumps
    Parameters:
        (bool) refresh: trigger sync with sun rest-api
    Return:
        (dict) sun time
    """
    from Time import suntime, Sun
    if refresh:
        return suntime()
    return Sun.TIME


def setclock(year, month, mday, hour, min, sec):
    """
    Set Localtime + RTC Clock manually
    :param year
    :param month
    :param mday
    :param hour
    :param min
    :param sec
    :return: localtime
    """
    set_time(year, month, mday, hour, min, sec)
    return localtime()


def rssi():
    """
    Show Wifi RSSI - wifi strength
    """
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


def pinmap(key='builtin'):
    """
    Get Logical pin by key runtime
    :param key str: logical pin name to resolve
    :return dict: key map
    """
    from microIO import pinmap_dump, get_pinmap
    map = get_pinmap()
    map[key] = pinmap_dump(key)[key]
    return map

@socket_stream
def alarms(clean=False, test=False, msgobj=None):
    """
    Show micrOS alarms - system error list
    :param clean bool: clean alarms, default: False
    :param test bool: create test alarms, set True
    :return dict: verdict
    """
    from Debug import errlog_get, errlog_add, errlog_clean
    if test:
        errlog_add('[ERR] TeSt ErRoR')
    if clean:
        errlog_clean(msgobj=msgobj)
    errcnt = errlog_get(msgobj=msgobj)
    return {'NOK alarm': errcnt} if errcnt > 0 else {'OK alarm': errcnt}


def dat_dump():
    """
    Generic .dat file dump
    - logged data from LMs
    """
    from os import listdir
    dats = (f for f in listdir() if f.endswith('.dat'))
    out = {}
    for dat in dats:
        with open(dat, 'r') as f:
            out[dat] = f.read()
    return out


def ifconfig():
    """
    Show network ifconfig
    """
    from Network import ifconfig
    return ifconfig()


def urequests_host_cache():
    """
    Debug function for urequests address caching
    - returns all known http(s) host addresses
    - cache only in memory
    """
    from urequests import host_cache
    return host_cache()


#######################
# LM helper functions #
#######################

def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'info', 'top', 'gclean', 'heartbeat', 'clock',\
           'setclock year month mday hour min sec',\
           'ntp', 'rssi', 'pinmap key="dhtpin"/None', 'alarms clean=False',\
           'sun refresh=False', 'ifconfig', 'memory_usage',\
           'disk_usage', 'dat_dump', 'urequests_host_cache'
