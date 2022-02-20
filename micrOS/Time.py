from socket import socket, getaddrinfo, AF_INET, SOCK_DGRAM, SOCK_STREAM
from machine import RTC
from utime import mktime, localtime
from network import WLAN, STA_IF
from re import match
from utime import sleep_ms
from Debug import errlog_add, console_write
from ConfigHandler import cfgput, cfgget


class Sun:
    TIME = {}
    UTC = cfgget('utc')  # STORED IN MINUTE


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


def ntptime():
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

    err = ''
    for _ in range(4 if cfgget('cron') else 2):
        try:

            t = getntp()
            tm = localtime(t + Sun.UTC * 60)
            # Get localtime + GMT shift
            RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
            return True
        except Exception as e:
            console_write("ntptime error.:{}".format(e))
            err = e
        sleep_ms(100)
    errlog_add("ntptime error: {}".format(err))
    return False


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
    console_write('   [http_get] url: {} ({})'.format(url, addr))
    s = socket()
    try:
        s.settimeout(tout)
        s.connect(addr)
        s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
        data = str(s.recv(bsize), 'utf8').splitlines()[-1]
    except Exception as e:
        errlog_add('[http_get] {} receive error: {}'.format(url, e))
    finally:
        s.close()
    console_write('   [http_get]    OK' if len(data) > 0 else '   [http_get]    NOK')
    return data


def __persistent_cache_manager(mode):
    """
    pds - persistent data structure
    modes:
        r - recover, s - save
    """
    if mode == 's':
        # SAVE CACHE
        temp = {}
        try:
            with open('sun.pds', 'w') as f:
                for k, v in Sun.TIME.items():
                    temp[k] = tuple([str(t) for t in v])
                f.write(';'.join(['{}:{}'.format(k, '-'.join(v)) for k, v in temp.items()]))
        finally:
            return
    try:
        print("-----------> DEBUG PRINT - CACHE LOAD")
        # RESTORE CACHE
        with open('sun.pds', 'r') as f:
            buff = {data.split(':')[0]: data.split(':')[1].split('-') for data in f.read().strip().split(';')}
            for k, v in buff.items():
                Sun.TIME[k] = tuple([int(e) for e in v])
    except:
        pass


def suntime():
    """
    :param lat: latitude
    :param lng: longitude
    :return: raw string / query output
    """

    if not cfgget('cron'):
        msg = "Cron: {} - SKIP sync".format(cfgget('cron'))
        console_write(msg)
        return msg

    console_write('[suntime] api sync started ...')
    # Get latitude, longitude, timezone, utc offset by external ip
    url = 'http://ip-api.com/json/?fields=lat,lon,timezone,offset'
    location_keys = ('lat', 'lon', 'timezone', 'offset')
    location = http_get(url, 512)
    parsed = {}
    try:
        parsed = {key: match('.+?{}.+?([0-9.a-zA-Z/]+)'.format(key), location).group(1) for key in location_keys}
        # Save utc offset in Sun class and micrOS config
        Sun.UTC = int(int(parsed['offset']) / 60)  # IN MINUTE
        cfgput('utc', Sun.UTC, True)
    except Exception as e:
        errlog_add('ip-api parse error: {}'.format(e))

    # Get sunrise-sunset + utc offset
    lat = parsed.get('lat', None)
    lon = parsed.get('lon', None)
    sun = {}
    if not (lat is None or lon is None):
        url = 'https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date=today&formatted=0'.format(lat=lat, lon=lon)
        sun_keys = ('sunrise', 'sunset')
        sun = http_get(url, 660)
        try:
            sun = {key: match('.+?results.+?{}.+?T([0-9:]+)'.format(key), sun).group(1).split(':') for key in sun_keys}
        except Exception as e:
            errlog_add('sunrise-api parse error: {}'.format(e))
        for key in sun_keys:
            sun[key] = [int(v) for v in sun[key]]
            sun[key][0] += int(Sun.UTC / 60)         # TODO: Handle UTC MINUTE OFFSET!
            sun[key] = tuple(sun[key])
    # Save to global variable for later access
    if sum([1 for _ in sun]) > 0:
        Sun.TIME = sun
        __persistent_cache_manager('s')
        console_write('[suntime] sync done and cached')
        return sun
    __persistent_cache_manager('r')
    console_write('[suntime] loaded from cache')
    return Sun.TIME


# Initial suntime cache load (for AP mode)
__persistent_cache_manager('r')
