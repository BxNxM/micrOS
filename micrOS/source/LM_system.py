from utime import localtime
from Common import socket_stream
from Network import get_mac, sta_high_avail
from Time import ntp_time, set_time, uptime


def memory_usage():
    """
    Calculate used micropython memory (ram)
    return: memory usage %, memory usage in bytes
    """
    try:
        from gc import mem_free, mem_alloc, collect
    except:
        from simgc import mem_free, mem_alloc, collect  # simulator mode
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
    from os import statvfs, getcwd
    fs_stat = statvfs(getcwd())
    fs_size = fs_stat[0] * fs_stat[2]
    fs_free = fs_stat[0] * fs_stat[3]
    used_space = fs_size - fs_free
    used_fs_percent = round(used_space / fs_size * 100, 1)
    return {'percent': used_fs_percent, 'fs_used': used_space}


@socket_stream
def info(msgobj=None):
    """
    Show system info message
    - cpu clock, ram, free fs, upython, board, mac addr, uptime
    """
    from machine import freq
    from os import uname
    msg_buffer = []

    def _reply(msg):
        nonlocal msg_buffer
        try:
            if msgobj is None:
                # write buffer
                msg_buffer.append(msg)
            else:
                # write socket buffer
                msgobj(msg)
        except Exception as e:
            # fallback: write buffer
            msg_buffer.append(f"{msg} ({e})")

    _reply('CPU clock: {} [MHz]'.format(int(freq() * 0.0000001)))
    _reply('Mem usage: {} %'.format(memory_usage()['percent']))
    _reply('FS usage: {} %'.format(disk_usage()['percent']))
    _reply('upython: {}'.format(uname()[3]))
    _reply('board: {}'.format(uname()[4]))
    try:
        _reply('mac: {}'.format(get_mac()))
    except:
        _reply('mac: n/a')
    _reply('uptime: {}'.format(uptime()))
    return '\n'.join(msg_buffer)


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
    return "{}  {}\nWD: {} YD: {}".format('.'.join(buff[0:3]), ':'.join(buff[3:6]), buff[6], buff[7])


def ntp():
    """
    Trigger NTP time sync
    """
    from ConfigHandler import cfgget
    try:
        # Automatic setup - over wifi - ntp
        state = ntp_time()
        return state, localtime()
    except Exception as e:
        return False, "ntp error:{}".format(e)


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


@socket_stream
def cachedump(cdel=None, msgobj=None):
    """
    Cache system persistent data storage files (.pds)
    """
    if cdel is None:
        # List pds files aka application cache
        from os import listdir
        msg_buf = []
        for pds in (_pds for _pds in listdir() if _pds.endswith('.pds')):
            with open(pds, 'r') as f:
                if msgobj is None:
                    msg_buf.append('{}: {}'.format(pds, f.read()))
                else:
                    msgobj('{}: {}'.format(pds, f.read()))
        return msg_buf if len(msg_buf) > 0 else ''
    # Remove given pds file
    from os import remove
    try:
        remove('{}.pds'.format(cdel))
        return '{}.pds delete done.'.format(cdel)
    except:
        return '{}.pds not exists'.format(cdel)


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
    from LogicalPins import pinmap_dump, get_pinmap
    map = get_pinmap()
    map[key] = pinmap_dump(key)[key]
    return map


def ha_sta():
    """
    Check and repair STA network mode
    """
    return sta_high_avail()


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


def ifconfig():
    """
    Show network ifconfig
    """
    from Network import ifconfig
    return ifconfig()


#######################
# LM helper functions #
#######################

def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'info', 'gclean', 'heartbeat', 'clock',\
           'setclock year month mday hour min sec',\
           'ntp', 'rssi', 'cachedump cdel="rgb.pds/None"',\
           'pinmap key="dhtpin"/None', 'ha_sta', 'alarms clean=False',\
           'sun refresh=False', 'ifconfig', 'memory_usage', 'disk_usage'
