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
            s.sendto(NTP_QUERY, addr)       # return with sendto response
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
    errlog_add("[ERR] ntptime error: {}".format(err))
    return False


def http_get(url, bsize=512, tout=3):
    """
    :param url: url param for http get
    :param bsize: buffer size for response msg
    :param tout: timeout for response
    :return: data string
    """
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
        # Send the http get query
        s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
        # Get last line of http response
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
    # Search keys in http request response
    location_keys = ('lat', 'lon', 'timezone', 'offset')
    sun_keys = ('sunrise', 'sunset')

    # IP-API REQUEST HANDLING
    # Get latitude, longitude, timezone, utc offset by external ip
    url = 'http://ip-api.com/json/?fields=lat,lon,timezone,offset'
    response = http_get(url, 512)
    location = {}
    try:
        location = {key: match('.+?{}.+?([0-9.a-zA-Z/]+)'.format(key), response).group(1) for key in location_keys}
        # Save utc offset in Sun class and micrOS config
        Sun.UTC = int(int(location['offset']) / 60)  # IN MINUTE
        cfgput('utc', Sun.UTC, True)
    except Exception as e:
        errlog_add('ip-api parse error: {}'.format(e))
    # Get sunrise-sunset + utc offset
    lat = location.get('lat', None)
    lon = location.get('lon', None)

    # SUNSET-SUNRISE API REQUEST HANDLING
    sun = {}
    if not (lat is None or lon is None):
        url = 'https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&date=today&formatted=0'.format(lat=lat, lon=lon)
        response = http_get(url, 660)
        try:
            sun = {key: match('.+?results.+?{}.+?T([0-9:]+)'.format(key), response).group(1).split(':') for key in sun_keys}
        except Exception as e:
            errlog_add('sunrise-api parse error: {} data: {}'.format(e, response))
    # Try to parse response by expected sun_keys
    try:
        for key in sun_keys:
            sun[key] = [int(v) for v in sun[key]]
            sun[key][0] += int(Sun.UTC / 60)
            sun[key] = tuple(sun[key])
    except:
        pass

    # Save to values class static variable for later access
    if sum([1 for _ in sun]) > 0:
        # Save and return with updated data
        Sun.TIME = sun
        __persistent_cache_manager('s')              # Using Sun.TIME
        console_write('[suntime] sync done and cached')
        return sun
    # Retrieve cached data and return
    __persistent_cache_manager('r')                  # Using Sun.TIME
    console_write('[suntime] loaded from cache')
    return Sun.TIME


# Initial suntime cache load (for AP mode)
__persistent_cache_manager('r')
