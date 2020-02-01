def mem_free():
    from gc import mem_free
    from machine import freq
    from micropython import mem_info
    return "CPU[Hz]: {}\nGC MemFree[byte]: {}".format(freq(), mem_free())

def listdir():
    from os import listdir
    return(listdir())

def reboot():
    from machine import reset
    reset()

def wifi_rssi(essid=None):
    from Wifi import wifi_rssi
    from ConfigHandler import cfg
    if essid is None:
        return(wifi_rssi(cfg.get('sta_essid')))
    else:
        return(wifi_rssi(essid))

def wifi_scan():
    from Wifi import network_wifi_scan
    return(network_wifi_scan())

def add2numbs(x, y):
    return "{} + {} = {}".format(x, y, x+y)
