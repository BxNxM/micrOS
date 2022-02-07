from socket import socket, getaddrinfo, AF_INET, SOCK_DGRAM, SOCK_STREAM
from machine import RTC
from utime import mktime, localtime
from network import WLAN, STA_IF
from Debug import errlog_add
from re import match
from ConfigHandler import cfgput

SUNTIME = {}


def settime(year, month, mday, hour, min, sec):
    """
    Set Localtime + RTC Clock manually
        https://docs.micropython.org/en/latest/library/machine.RTC.html
    """
    # Make time from tuple to sec
    time_sec = mktime((year, month, mday, hour, min, sec, 0, 0))
    # Set localtime
    localtime(time_sec)
    # Set RTC
    RTC().datetime((year, month, mday, 0, hour, min, sec, 0))
    return True


def ntptime(utc_shift=0):
    """
    Set NTP time with utc shift
    :param utc_shift: +/- hour (int)
    :return: None
    """

    if not WLAN(STA_IF).isconnected():
        errlog_add("STA not connected: ntptime")
        return False

    import struct

    def getntp():
        host = "pool.ntp.org"
        # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        NTP_DELTA = 3155673600
        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B
        addr = getaddrinfo(host, 123)[0][-1]
        s = socket(AF_INET, SOCK_DGRAM)
        try:
            s.settimeout(2)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
        finally:
            s.close()
        val = struct.unpack("!I", msg[40:44])[0]
        return val - NTP_DELTA

    t = getntp()
    tm = localtime(t + utc_shift * 3600)
    # Get localtime + GMT shift
    RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
    return True


def http_get(url, bsize=512, tout=3):
    data = ''

    if not WLAN(STA_IF).isconnected():
        errlog_add("[http_get] STA not connected")
        return data

    _, _, host, path = url.split('/', 3)
    try:
        addr = getaddrinfo(host, 80, AF_INET, SOCK_STREAM)[0][-1]
    except Exception as e:
        errlog_add('[http_get] resolve error: {}'.format(e))
        return data
    # HTTP GET
    s = socket()
    try:
        s.settimeout(tout)
        s.connect(addr)
        s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
        data = str(s.recv(bsize), 'utf8').splitlines()[-1]
    except Exception as e:
        errlog_add('[http_get] receive error: {}'.format(e))
    finally:
        s.close()
    return data


def suntime():
    """
    :param lat: latitude
    :param lng: longitude
    :return: raw string / query output
    """
    global SUNTIME

    # Get latitude, longitude, timezone by external ip
    url = 'http://ip-api.com/json/'
    location_keys = ('lat', 'lon', 'timezone')
    location = http_get(url, 550)
    parsed = {key: match('.+?{}.+?([0-9.a-zA-Z/]+)'.format(key), location).group(1) for key in location_keys}

    # Get utc offset by timezone + overwrite gmttime (config parameter)
    timezone = parsed.get('timezone', None)
    utc_offset = 0
    if timezone is not None:
        url = 'http://worldtimeapi.org/api/timezone/{}'.format(timezone)
        utc_offset = http_get(url, 980)
        utc_offset = match('.+?utc_offset...([+-:0-9]+)', utc_offset).group(1)
        try:
            utc_offset = int(utc_offset.split(':')[0])
            cfgput('gmttime', utc_offset, True)         # TODO: handle all utc values!!! (only whole utc offsets are supported now)
        except Exception as e:
            errlog_add('utc offset error: {}'.format(e))
            utc_offset = 0

    # Get sunrise-sunset + utc offset
    lat = parsed.get('lat', None)
    lon = parsed.get('lon', None)
    if not (lat is None or lon is None):
        url = 'https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date=today&formatted=0'.format(lat=lat, lon=lon)
        sun_keys = ('sunrise', 'sunset')
        sun = http_get(url, 660)
        sun = {key: match('.+?results.+?{}.+?T([0-9:]+)'.format(key), sun).group(1).split(':') for key in sun_keys}
        for key in sun_keys:
            sun[key] = [int(v) for v in sun[key]]
            sun[key][0] += utc_offset
            sun[key] = tuple(sun[key])
    # Save to global variable for later access
    SUNTIME = sun
    return sun