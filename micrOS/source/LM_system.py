from uos import statvfs, getcwd, listdir, uname
from utime import localtime
from network import WLAN, STA_IF, AP_IF
from binascii import hexlify
from Common import socket_stream, console
from Network import get_mac, ifconfig as network_config
from Time import ntp_time, set_time, uptime
from Tasks import Manager
from Types import resolve
from Notify import Notify

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

    buffer = top()
    buffer.update({'CPU clock [MHz]': int(freq() * 0.0000001), 'upython': uname()[3],
              'board': uname()[4], 'uptime': uptime()})
    try:
        buffer['mac'] = hexlify(get_mac(), ':').decode()
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
    console("<3 heartbeat <3")
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


def setclock(year, month, mday, hour, minute, sec):
    """
    Set Localtime + RTC Clock manually
    :param year
    :param month
    :param mday
    :param hour
    :param minute
    :param sec
    :return: localtime
    """
    set_time(year, month, mday, hour, minute, sec)
    return localtime()


def rssi():
    """
    Show Wifi RSSI - wifi strength
    """
    if ifconfig()[0] == "STA":
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
    return {'Unavailable': -90}


def list_stations():
    """
    AccessPoint mode "router"
    - list connected devices
    """
    if ifconfig()[0] == "AP":
        ap = WLAN(AP_IF)
        stations = ap.status('stations')
        connected_devices = []
        for sta in stations:
            mac_address, mac_rssi = '', ''
            if len(sta) > 0:
                mac_bytes = sta[0]
                mac_address = hexlify(mac_bytes, ':').decode()
            elif len(sta) > 1:
                mac_rssi = sta(1)
            connected_devices.append((mac_address, mac_rssi))
        return connected_devices
    return [("NoAP", '')]


def pinmap(keys='builtin irq1 irq2 irq3 irq4'):
    """
    Get Logical pin by key runtime
    :param keys str: logical pin name or names to resolve
    :return dict: key map
    """
    from microIO import pinmap_search, pinmap_info
    map = pinmap_info()
    keys = keys.split()
    map["search"] = pinmap_search(keys)
    return map


@socket_stream
def alarms(clean=False, msgobj=None):
    """
    Show micrOS alarms - system error list
    :param clean bool: clean alarms, default: False
    :return dict: verdict
    """
    from Logger import log_clean, syslog
    if clean:
        log_clean(msgobj=msgobj)
    errcnt = -1 if syslog is None else syslog(msgobj=msgobj)
    return {'NOK alarm': errcnt} if errcnt > 0 else {'OK alarm': errcnt}


def ifconfig():
    """
    Show network ifconfig
    """
    return network_config()


def urequest_hosts():
    """
    Debug function for urequests address caching
    - returns all known http(s) host addresses
    - cache only in memory
    """
    from urequests import host_cache
    return host_cache()


def notifications(enable=None):
    """
    Global notifications control for micrOS
    :param enable: True: Enable notifications / False: Disable notifications
    return: state verdict
    """
    return Notify.notifications(state=enable)

#######################
# LM helper functions #
#######################

def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('info', 'TEXTBOX top', 'gclean', 'heartbeat', 'clock',
                    'setclock year month mday hour minute sec',
                    'ntp', 'rssi', 'list_stations', 'pinmap key="dhtpin"/None', 'alarms clean=False',
                    'notifications enable=<None,True,False>',
                    'sun refresh=False', 'ifconfig', 'memory_usage',
                    'disk_usage', 'urequest_hosts'), widgets=widgets)
