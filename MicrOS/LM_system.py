def memfree():
    from gc import mem_free
    from machine import freq
    from micropython import mem_info
    return "CPU[Hz]: {}\nGC MemFree[byte]: {}".format(freq(), mem_free())

def gccollect():
    from gc import collect
    collect()
    return memfree()

def reboot():
    from machine import reset
    try:
        from LM_oled_128x64i2c import poweroff
        poweroff()
    except:
        pass
    reset()

def heartbeat():
    from ProgressLED import toggle
    from time import sleep
    toggle()
    sleep(0.1)
    toggle()

def time():
    from time import localtime
    return localtime()

def setNTP():
    from Network import setNTP_RTC
    state = setNTP_RTC()
    if state:
        return time()
    else:
        return "NTP-RTC setup failed."

def wifirssi(essid=None):
    try:
        from Network import wifi_rssi
    except Exception as e:
        return "Network.wifi_rssi import error: " + str(e)
    if essid is None:
        from ConfigHandler import cfgget
        return(wifi_rssi(cfgget('staessid')))
    else:
        return(wifi_rssi(essid))

def help():
    return ('memfree', 'gccollect', 'reboot', 'heartbeat', 'time')
