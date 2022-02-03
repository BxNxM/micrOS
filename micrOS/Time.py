from socket import socket, getaddrinfo, AF_INET, SOCK_DGRAM
from machine import RTC
from utime import mktime, localtime
from network import WLAN, STA_IF
from Debug import errlog_add


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


def suntime(lat=51.509865, lng=-0.118092):
    """
    :param lat: latitude
    :param lng: longitude
    :return: raw string / query output
    """
    if not WLAN(STA_IF).isconnected():
        errlog_add("STA not connected: suntime")
        return '', ''

    url = 'https://api.sunrise-sunset.org/json?lat={lat}&lng={lng}&date=today&formatted=0'.format(lat=lat, lng=lng)
    _, _, host, path = url.split('/', 3)
    try:
        addr = getaddrinfo(host, 80)[0][-1]
    except Exception as e:
        errlog_add('suntime: resolve failed: {}'.format(e))
        return '', ''
    # HTTP GET
    s = socket()
    try:
        s.settimeout(3)
        s.connect(addr)
        s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
        data = s.recv(1024)
    finally:
        s.close()
    # BYTE CONVERT AND PARSE
    try:
        data = str(data, 'utf8').splitlines()
        data = data[2], data[-1]
    except Exception as e:
        errlog_add('suntime: query failed: {}'.format(e))
        return '', ''
    return data
