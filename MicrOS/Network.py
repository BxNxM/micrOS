from network import AP_IF, STA_IF, WLAN
from time import sleep, localtime, time

try:
    from ConfigHandler import console_write, cfgget, cfgput
except Exception as e:
    print("Failed to import ConfigHandler: {}".format(e))
    console_write = None

def setNTP_RTC():
    from ntptime import settime
    from machine import RTC

    for _ in range(4):
        if WLAN(STA_IF).isconnected():
            break
        sleep(0.5)

    if WLAN(STA_IF).isconnected():
        for _ in range(4):
            try:
                settime()
                rtc = RTC()
                (year, month, mday, hour, minute, second, weekday, yearday) = localtime(time() + int(cfgget('gmttime'))*3600)
                rtc.datetime((year, month, mday, 0, hour, minute, second, 0))
                console_write("NTP setup DONE: {}".format(localtime()))
                return True
            except Exception as e:
                console_write("NTP setup errer.:{}".format(e))
            sleep(0.5)
    else:
        console_write("NTP setup errer: STA not connected!")
    return False

#########################################################
#                                                       #
#                  SET WIFI STA MODE                    #
#                                                       #
#########################################################
def set_wifi(essid, pwd, timeout=50):
    console_write('[NW: STA] SET WIFI: {}'.format(essid))

    # Disable AP mode
    ap_if = WLAN(AP_IF)
    if ap_if.active():
        ap_if.active(False)
    del ap_if

    # Set STA and Connect
    sta_if = WLAN(STA_IF)
    sta_if.active(True)
    if not sta_if.isconnected():
        console_write('\t| [NW: STA] CONNECT TO NETWORK {}'.format(essid))
        if essid in [ wifispot[0].decode('utf-8') for wifispot in sta_if.scan() ]:
            # connect to network
            sta_if.connect(essid, pwd)
            # wait for connection, with timeout set
            while not sta_if.isconnected() and timeout > 0:
                console_write("\t| [NW: STA] Waiting for connection... " + str(timeout) + "/50" )
                timeout -= 1
                sleep(0.4)
        else:
            console_write("\t| [NW: STA] Wifi network was NOT found: {}".format(essid))
            return False
        console_write("\t|\t| [NW: STA] network config: " + str(sta_if.ifconfig()))
        cfgput("devip", str(sta_if.ifconfig()[0]))
        console_write("\t|\t| [NW: STA] CONNECTED: " + str(sta_if.isconnected()))
    else:
        console_write("\t| [NW: STA] ALREADY CONNECTED TO {}".format(essid))
        cfgput("devip", str(sta_if.ifconfig()[0]))
    return sta_if.isconnected()

#########################################################
#                                                       #
#               SET WIFI ACCESS POINT MODE              #
#                                                       #
#########################################################
def set_access_point(_essid, _pwd, _authmode=3):
    console_write("[NW: AP] SET AP MODE: {} - {} - auth mode: {}".format(_essid, _pwd, _authmode))

    sta_if = WLAN(STA_IF)
    if sta_if.isconnected():
        sta_if.active(False)

    ap_if = WLAN(AP_IF)
    ap_if.active(True)
    # Set WiFi access point name (formally known as ESSID) and WiFi authmode (2): WPA2
    try:
        console_write("[NW: AP] Configure")
        ap_if.config(essid=_essid, password=_pwd, authmode=_authmode)
    except Exception as e:
        console_write("[NW: AP] Config Error".format(e))
    if ap_if.active() and str(ap_if.config('essid')) == str(_essid) and ap_if.config('authmode') == _authmode:
        cfgput("devip", ap_if.ifconfig()[0])
    console_write("\t|\t| [NW: AP] network config: " + str(ap_if.ifconfig()))
    return ap_if.active()

#########################################################
#                                                       #
#          AUTOMATIC NETWORK CONFIGURATION              #
#IF STA AVAIBLE, IF NOT AP MODE                         #
#########################################################
def auto_network_configuration(essid=None, pwd=None, timeout=50, _essid=None, _pwd=None, _authmode=3, retry=3):
    # GET DATA - STA
    if essid is None:
        essid = cfgget("staessid")
    if pwd is None:
        pwd = cfgget("stapwd")
    # GET DATA - AP
    if _essid is None:
        _essid = cfgget("devfid")
    if _pwd is None:
        _pwd = cfgget("appwd")

    state = False
    while not state and retry > 0:
        retry -= 1
        state = set_wifi(essid, pwd, timeout)
        if not state:
            state = set_access_point(_essid, _pwd, _authmode)
            if state:
                cfgput("nwmd", "AP")
        else:
            cfgput("nwmd", "STA")
            setNTP_RTC()

#########################################################
#                                                       #
#                 GET WIFI STRENGHT                     #
#                                                       #
#########################################################
def network_wifi_scan():
    return [ i[0].decode("utf-8") for i in WLAN().scan() ]

def wifi_rssi(essid):
    """ GET SSID AND CHANNEL FOR THE SELECTED ESSID"""
    console_write("[WIFI RSSI METHOD] GET RSSI AND CHANNEL FOR GIVEN ESSID")
    rssi = None
    channel = None
    sta_if = WLAN(STA_IF)
    sta_if.active(True)
    # if sta not connected to the given essid
    if not sta_if.isconnected():
        return None, None, None, (None, 0)
    # if we are connected - get informations
    try:
        wifi_list = sta_if.scan()
    except:
        rssi = 0
        channel = None
        wifi_list = []
    for wifi_spot in wifi_list:
        if essid in str(wifi_spot):
            rssi = wifi_spot[3]
            channel = wifi_spot[2]
    # calculate human readable quality for rssi - hr_rssi_tupple: human readuble rssi tumpe [0]- string, [1]: number 0-4
    if rssi >= -30:
        hr_rssi_tupple = "Amazing", 4
    elif rssi >= -67:
        hr_rssi_tupple = "VeryGood", 3
    elif rssi >= -70:
        hr_rssi_tupple = "Okey", 2
    elif rssi >= -80:
        hr_rssi_tupple = "NotGood", 1
    elif rssi >= -90:
        hr_rssi_tupple = "Unusable", 0
    else:
        hr_rssi_tupple = "N/A", -1

    console_write("\t| essid, rssi, channel: " + str(essid) +", "+ str(rssi) +", "+ str(channel) +", "+ str(hr_rssi_tupple))
    return essid, rssi, channel, hr_rssi_tupple

