from utime import localtime
from Common import socket_stream
from Network import get_mac
from Time import ntptime, settime, suntime, Sun, uptime
from Debug import errlog_get, errlog_add, errlog_clean, console_write


@socket_stream
def info(msgobj=None):
    """
    Show system info message
    - cpu clock, ram, free fs, upython, board, mac addr, uptime
    """
    try:
        from gc import mem_free
    except:
        from simgc import mem_free  # simulator mode
    from os import statvfs, getcwd, uname
    from machine import freq

    msg_buffer = []

    def _reply(msg):
        nonlocal msg_buffer
        if msgobj is None:
            msg_buffer.append(msg)
        else:
            msgobj(msg)

    fs_stat = statvfs(getcwd())
    fs_size = fs_stat[0] * fs_stat[2]
    fs_free = fs_stat[0] * fs_stat[3]
    mem = mem_free()
    _reply('CPU clock: {} [MHz]'.format(int(freq() * 0.0000001)))
    _reply('Free RAM: {} kB {} byte'.format(int(mem / 1024), int(mem % 1024)))
    _reply('Free fs: {} %'.format(int((fs_free / fs_size) * 100)))
    _reply('upython: {}'.format(uname()[3]))
    _reply('board: {}'.format(uname()[4]))
    _reply('mac: {}'.format(get_mac()))
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
    console_write("<3 heartbeat <3")
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
        state = ntptime()
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
    settime(year, month, mday, hour, min, sec)
    return localtime()


def module(unload=None):
    """
    List / unload Load Modules
    :param unload str: module name to unload
    :param unload None: list active modules
    :return str: verdict
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


@socket_stream
def lmpacman(lm_del=None, msgobj=None):
    """
    Load module package manager
    :param lm_del str: LM_<loadmodulename.py/.mpy>
    :param lm_del None: list available load modules
    - Add name without LM_ but with extension!
    """
    from os import listdir, remove
    if lm_del is not None and lm_del.endswith('py'):
        # Check LM is in use
        if 'system.' in lm_del:
            return 'Load module {} is in use, skip delete.'.format(lm_del)
        remove('LM_{}'.format(lm_del))
        return 'Delete module: {}'.format(lm_del)
    # Dump available LMs
    msg_buf = []
    for k in (res.replace('LM_', '') for res in listdir() if 'LM_' in res):
        if msgobj is None:
            msg_buf.append('   {}'.format(k))
        else:
            msgobj('   {}'.format(k))
    return msg_buf if len(msg_buf) > 0 else ''


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
    - able to restart the system -> wifi reconnect
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
    """
    Show micrOS alarms - system error list
    :param clean bool: clean alarms, default: False
    :param test bool: create test alarms, set True
    :return dict: verdict
    """
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


@socket_stream
def micros_checksum(msgobj=None):
    from hashlib import sha256
    from binascii import hexlify
    from os import listdir
    from ConfigHandler import cfgget

    for f_name in (_pds for _pds in listdir() if _pds.endswith('py')):
        with open(f_name, 'rb') as f:
            cs = hexlify(sha256(f.read()).digest()).decode('utf-8')
        msgobj("{} {}".format(cs, f_name))
    return "micrOS version: {}".format(cfgget('version'))


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
           'ntp', 'module unload="LM_rgb/None"', \
           'rssi', 'cachedump cdel="rgb.pds/None"', 'lmpacman lm_del="LM_rgb.py/None"',\
           'pinmap key="dhtpin"/None', 'ha_sta', 'alarms clean=False',\
           'sun refresh=False', 'ifconfig', 'micros_checksum'
