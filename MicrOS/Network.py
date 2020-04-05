#################################################################
#                           IMPORTS                             #
#################################################################
from network import AP_IF, STA_IF, WLAN
from time import sleep, localtime, time
from ntptime import settime
from machine import RTC
from ConfigHandler import console_write, cfgget, cfgput

#################################################################
#                      NTP & RTC TIME SETUP                     #
#################################################################


def setNTP_RTC():
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

#################################################################
#                   GET DEVICE UID BY MAC ADDRESS               #
#################################################################


def set_uid_macaddr_hex(sta_if=None):
    uid = "n/a"
    if sta_if is not None:
        uid = ""
        for ot in list(sta_if.config('mac')):
            uid += hex(ot)
    cfgput("hwuid", uid)


#################################################################
#                       SET WIFI STA MODE                       #
#################################################################


def set_wifi(essid, pwd, timeout=60):
    console_write('[NW: STA] SET WIFI: {}'.format(essid))
    essid_found = False

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
        # Scan wifi network - retry workaround
        for _ in range(0, 2):
            if essid in [ wifispot[0].decode('utf-8') for wifispot in sta_if.scan() ]:
                essid_found = True
                console_write('\t| - [NW: STA] ESSID WAS FOUND {}'.format(essid_found))
                break
            sleep(1)
        # Connect to the located wifi network
        if essid_found:
            # connect to network
            sta_if.connect(essid, pwd)
            # wait for connection, with timeout set
            while not sta_if.isconnected() and timeout > 0:
                console_write("\t| [NW: STA] Waiting for connection... " + str(timeout) + "/60" )
                timeout -= 1
                sleep(0.5)
            # Set static IP - here because some data comes from connection.
            if __set_wifi_dev_static_ip(sta_if):
                sta_if.disconnect()
                del sta_if
                return set_wifi(essid, pwd)
        else:
            console_write("\t| [NW: STA] Wifi network was NOT found: {}".format(essid))
            return False
        console_write("\t|\t| [NW: STA] network config: " + str(sta_if.ifconfig()))
        cfgput("devip", str(sta_if.ifconfig()[0]))
        set_uid_macaddr_hex(sta_if)
        console_write("\t|\t| [NW: STA] CONNECTED: " + str(sta_if.isconnected()))
    else:
        console_write("\t| [NW: STA] ALREADY CONNECTED TO {}".format(essid))
        cfgput("devip", str(sta_if.ifconfig()[0]))
        set_uid_macaddr_hex(sta_if)
    return sta_if.isconnected()


def __set_wifi_dev_static_ip(sta_if):
    reconfigured = False
    console_write("[NW: STA] Set device static IP.")
    stored_ip = cfgget('devip')
    if 'n/a' not in stored_ip.lower() and '.' in stored_ip:
        conn_ips = list(sta_if.ifconfig())
        if conn_ips[0] != stored_ip and conn_ips[-1].split('.')[0:1] == stored_ip.split('.')[0:1]:      # check change and ip type
            conn_ips[0] = stored_ip
            console_write("\t| [NW: STA] DEV. StaticIP: {}".format(stored_ip))
            try:
                # IP address, subnet mask, gateway and DNS server
                sta_if.ifconfig(tuple(conn_ips))
                reconfigured = True
            except Exception as e:
                console_write("\t\t| [NW: STA] StaticIP conf. failed: {}".format(e))
        else:
            console_write("[NW: STA] StaticIP was already set: {}".format(stored_ip))
    else:
        console_write("[NW: STA] IP was not stored: {}".format(stored_ip))
    return reconfigured


#################################################################
#                    SET WIFI ACCESS POINT MODE                 #
#################################################################


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

#################################################################
#              AUTOMATIC NETWORK CONFIGURATION                  #
#               IF STA AVAIBLE, IF NOT AP MODE                  #
#################################################################


def auto_network_configuration(_authmode=3, retry=3):
    # GET DATA - STA
    essid = cfgget("staessid")
    pwd = cfgget("stapwd")
    # GET DATA - AP
    _essid = cfgget("devfid")
    _pwd = cfgget("appwd")

    for _ in range(0, retry):
        # Reset dev (static)ip if previous nw setup was AP
        if cfgget("nwmd") == "AP":
            cfgput("devip", "n/a")
        # SET WIFI (STA) MODE
        state = set_wifi(essid, pwd)
        if state:
            # Save STA NW mode
            cfgput("nwmd", "STA")
            # Set NTP - RTC
            setNTP_RTC()
            # BREAK - STA mode successfully  configures
            break
        else:
            # SET AP MODE
            state = set_access_point(_essid, _pwd, _authmode)
            if state:
                # Save AP NW mode
                cfgput("nwmd", "AP")
                # BREAK - AP mode successfully  configures
                break

