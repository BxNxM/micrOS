from Common import socket_stream
from Debug import console_write


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


def pinmap(key='builtin'):
    """
    Get Logical pin by key runtime
    """
    from LogicalPins import physical_pin, get_pinmap
    return {key: physical_pin(key), 'pinmap': get_pinmap()}


#######################
# LM helper functions #
#######################

def help():
    return 'info', 'gclean', 'heartbeat', 'module unload="LM_rgb/None"', \
           'rssi', 'lmpacman lm_del="LM_rgb.py/None"', 'pinmap key="dhtpin/None"'
