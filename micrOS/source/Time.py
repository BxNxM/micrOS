"""
Module is responsible for Time related functions
- ntp, clock setup, uptime
- time tags support (cron): sunset, sunrise

Designed by Marcell Ban aka BxNxM
"""

from socket import socket, getaddrinfo, AF_INET, SOCK_DGRAM
from re import compile as re_comp
from struct import unpack
from machine import RTC
from network import WLAN, STA_IF
from utime import sleep_ms, time, mktime, localtime

from Config import cfgput, cfgget
from Debug import errlog_add, console_write
from urequests import get as http_get
from Files import OSPath, path_join


class Sun:
    TIME = {}
    UTC = cfgget('utc')  # STORED IN MINUTE
    BOOTIME = None       # Initialize BOOTIME: Not SUN, but for system uptime
    FILE_CACHE = path_join(OSPath.DATA, 'sun.cache')


def set_time(year, month, mday, hour, minute, sec):
    """
    Set Localtime + RTC Clock manually + update BOOTIME/uptime
        https://docs.micropython.org/en/latest/library/machine.RTC.html
    """
    # Make time from tuple to sec
    time_sec = mktime((year, month, mday, hour, minute, sec, 0, 0))
    # Set localtime
    localtime(time_sec)
    # Set RTC
    RTC().datetime((year, month, mday, 0, hour, minute, sec, 0))
    # (re)set uptime when settime - normally at boot time
    if Sun.BOOTIME is None:
        Sun.BOOTIME = time()
    return True


def ntp_time():
    """
    Set NTP time with utc shift + update BOOTIME/uptime
    :return: ntp date struct
    """
    if not WLAN(STA_IF).isconnected():
        errlog_add("STA not connected: ntptime")
        return False

    def get_ntp():
        host = "pool.ntp.org"
        # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        _ntp_delta = 3155673600
        _ntp_query = bytearray(48)
        _ntp_query[0] = 0x1B
        addr = getaddrinfo(host, 123)[0][-1]
        s = socket(AF_INET, SOCK_DGRAM)
        try:
            s.settimeout(2)
            s.sendto(_ntp_query, addr)       # return with sendto response
            msg = s.recv(48)
        finally:
            s.close()
        val = unpack("!I", msg[40:44])[0]
        return val - _ntp_delta

    err = ''
    for _ in range(4 if cfgget('cron') else 2):
        try:

            t = get_ntp()
            tm = localtime(t + Sun.UTC * 60)
            # Get localtime + GMT shift
            RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
            # Set bootup time - first time init
            if Sun.BOOTIME is None:
                Sun.BOOTIME = time()
            return True
        except Exception as e:
            console_write(f"ntptime error.:{e}")
            err = e
        sleep_ms(100)
    errlog_add(f"[ERR] ntptime: {err}")
    return False


def __sun_cache(mode):
    """
    File cache
    modes:
        r - recover, s - save
    """
    if mode == 's':
        # SAVE CACHE
        try:
            with open(Sun.FILE_CACHE, 'w') as f:
                cache = {k:tuple([str(t) for t in v]) for k, v in Sun.TIME.items()}
                f.write(';'.join([f'{k}:{"-".join(v)}' for k, v in cache.items()]))
        except:
            errlog_add("[ERR] Cannot write sun cache")
        return
    try:
        # RESTORE CACHE
        with open(Sun.FILE_CACHE, 'r') as f:
            buff = {data.split(':')[0]: data.split(':')[1].split('-')
                    for data in f.read().strip().split(';')}
            for k, v in buff.items():
                Sun.TIME[k] = tuple([int(e) for e in v])
    except:
        pass


def suntime():
    """
    GET sunrise and sunset time stumps for cron scheduling
    - url: http://ip-api.com/json
    - url: https://api.sunrise-sunset.org
    :return: sun dict {'sunset': (h:m:s), 'sunrise': (h:m:s)}
    """

    if not cfgget('cron'):
        msg = f"Cron: {cfgget('cron')} - SKIP sync"
        console_write(msg)
        return msg

    console_write('[suntime] api sync started ...')

    # IP-API REQUEST HANDLING
    # Get latitude, longitude, timezone, utc offset by external ip
    url = 'http://ip-api.com/json/?fields=lat,lon,timezone,offset'
    response = {}
    try:
        _, response = http_get(url, jsonify=True)
        lat = response.get('lat')
        lon = response.get('lon')
        Sun.UTC = int(response.get('offset') / 60)      # IN MINUTE
        cfgput('utc', Sun.UTC, True)
    except Exception as e:
        errlog_add(f'[ERR] ip-api: {e} data: {response}')
        return Sun.TIME

    # SUNSET-SUNRISE API REQUEST HANDLING
    # Get sunrise, sunset date times by lon, lat params
    sun = {'sunrise': (), 'sunset': ()}
    if not (lat is None or lon is None):
        url = f'http://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date=today&formatted=0'
        try:
            _, response = http_get(url, sock_size=512, jsonify=True)
            results = response.get('results')
            time_regex = re_comp(r'T([0-9:]+)')
            sun = {'sunrise': time_regex.search(results.get('sunrise')).group(1).split(':'),
                   'sunset': time_regex.search(results.get('sunset')).group(1).split(':')}
        except Exception as e:
            errlog_add(f'[ERR] sunrise-api: {e} data: {response}')
    # Try to parse response by expected sun_keys
    try:
        for key in sun:
            sun[key] = [int(val) for val in sun[key]]
            sun[key][0] += int(Sun.UTC / 60)
            sun[key] = tuple(sun[key])
    except Exception as e:
        errlog_add(f'sunrise-api parse error: {e} sun: {sun}')
        # Retrieve cached data and return
        __sun_cache('r')  # Using Sun.TIME
        console_write('[suntime] loaded from cache')
        return Sun.TIME

    # Save to values class static variable for later access
    # Save and return with updated data
    Sun.TIME = sun
    __sun_cache('s')              # Using Sun.TIME
    console_write('[suntime] sync done and cached')
    return sun


def uptime(update=False):
    """
    Get system uptime based on Sun.BOOTIME (time.time() stored at bootup)
    :param update: update BOOTIME param for system uptime (AP mode)
    """
    if update:
        Sun.BOOTIME = time()
    if Sun.BOOTIME is None:
        return "No time function was initialized..."
    delta = int(time() - Sun.BOOTIME)
    days, hours, minutes, sec = delta // 86400, (delta % 86400) // 3600, delta / 60 % 60, delta % 60
    return f"{int(days)} {int(hours)}:{int(minutes)}:{int(sec)}"


# Initial suntime cache load (for AP mode)
__sun_cache('r')
