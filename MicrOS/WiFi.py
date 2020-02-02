from network import AP_IF, STA_IF, WLAN
from time import sleep

try:
    from ConfigHandler import console_write, cfg
except Exception as e:
    print("Failed to import ConfigHandler: {}".format(e))
    console_write = None
    cfg = None

#########################################################
#                                                       #
#               SIMPLE WIFI INFO GETTER                 #
#                                                       #
#########################################################
def wifi_info():
    wifi_info_dict = {}

    # the access point
    ap_if = WLAN(AP_IF)

    # station mode - connect to wifi
    sta_if = WLAN(STA_IF)

    # turn access point on:
    #ap_if.active(True)
    # turn access point off:
    #ap_if.active(False)

    # turn station mode on:
    #sta_if.active(True)
    # turn station mode off:
    #sta_if.active(False)

    # turn on station mode:
    #sta_if.connect('<your ESSID>', '<your password>')
    #sta_if.config('password')

    wifi_info_dict = {  'ap_state': str(ap_if.active()),
                        'sta_state': str(sta_if.active()),
                        'ap_isconnected': str(ap_if.isconnected()),
                        'sta_isconnected': str(sta_if.isconnected()),
                        'ap_iplist': ap_if.ifconfig(),
                        'sta_iplist': sta_if.ifconfig(),
    }
    if wifi_info_dict['ap_state'] == "True":
        #wifi_info_dict['ap_avaible_networks'] = str(ap_if.scan())
        wifi_info_dict['ap_avaible_networks'] = str(None)
    else:
        wifi_info_dict['ap_avaible_networks'] = str(None)

    if wifi_info_dict['sta_state'] == "True":
        wifi_info_dict['sta_avaible_networks'] = str(sta_if.scan())
        #wifi_info_dict['sta_avaible_networks'] = str(None)
    else:
        wifi_info_dict['sta_avaible_networks'] = str(None)

    #console_write(wifi_info_dict)
    return wifi_info_dict

#########################################################
#                                                       #
#                  SET WIFI STA MODE                    #
#                                                       #
#########################################################
def set_wifi(essid, pwd, timeout=50, ap_auto_disable=True, essid_force_connect=False):
    """ WIFI SETTER - EXTAR PARAMETERS: ACCESS POINT AUTO DISABLE WHEN STATION MODE IS ON, ESSID DISCONNECT BEFORE CONNECT SELECTED SSID """
    console_write("[SET_WIFI METHOD] SET WIFI NETWORK:\nparameters: essid,\t\t\tpwd,\t\ttimeout,\tap_auto_disable,\tessid_force_connect\n            " + \
                             str(essid) +",\t"+  str(pwd) +",\t"+ str(timeout) +",\t\t"+ str(ap_auto_disable) +",\t\t\t"+ str(essid_force_connect))
    if ap_auto_disable:
        ap_if = WLAN(AP_IF)
        if ap_if.active():
            ap_if.active(False)

    sta_if = WLAN(STA_IF)
    sta_if.active(True)
    is_essid_exists = False
    # disconnect before connect to selected essid *** normally micropython framework connected to last known wlan network automaticly
    if essid_force_connect and sta_if.isconnected():
        console_write("\t| disconnect from wifi (sta)")
        sta_if.disconnect()
    # connet if we are not connected yet
    if not sta_if.isconnected():
        console_write('\t| connecting to network... ')
        sta_if.active(True)
        for wifi_spot in sta_if.scan():
            if essid in str(wifi_spot):
                is_essid_exists = True
                # connect to network
                sta_if.connect(essid, pwd)
                # wait for connection, with timeout set
                while not sta_if.isconnected() and timeout > 0:
                    console_write("Waiting for connection... " + str(timeout) + "/50" )
                    timeout -= 1
                    sleep(0.4)
        console_write("\t|\t| network config: " + str(sta_if.ifconfig()))
        cfg.put("devip", str(sta_if.ifconfig()[0]))
        console_write("\t|\t| WIFI SETUP STA: " + str(sta_if.isconnected()))
    else:
        console_write("\t| already conneted (sta)")
        cfg.put("devip", str(sta_if.ifconfig()[0]))
        # we are connected already
        for wifi_spot in sta_if.scan():
            if essid in str(wifi_spot):
                is_essid_exists = True
    # return bool:is connected to network, bool: is essid found
    return sta_if.isconnected(), is_essid_exists

#########################################################
#                                                       #
#                 GET WIFI STRENGHT                     #
#                                                       #
#########################################################
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

    console_write("\t| essid, rssi, channel: " + str(essid) +", "+ str(rssi) +", "+ str(channel) +", "+ str(hr_rssi_tupple))
    return essid, rssi, channel, hr_rssi_tupple

#########################################################
#                                                       #
#               SET WIFI ACCESS POINT MODE              #
#                                                       #
#########################################################
def set_access_point(_essid, _pwd, _channel=11, sta_auto_disable=True):
    """ SET ACCESS POINT WITH CUSTOM ESSID, CHANNEL, FORCE MODE LIKE SET WIFI METHOD...."""
    console_write("[SET ACCESS POUNT METHOD] SET ACCESS POINT MODE:\n_essid,\t\t_pwd,\t_channel,\tsta_auto_disable\n" +\
                             str(_essid) +",\t"+ str(_pwd) +",\t"+  str(_channel) +",\t\t"+ str(sta_auto_disable))
    if sta_auto_disable:
        sta_if = WLAN(STA_IF)
        if sta_if.isconnected():
            sta_if.active(False)

    ap_if = WLAN(AP_IF)
    ap_if.active(True)
    is_success = False
    # Set WiFi access point name (formally known as ESSID) and WiFi channel
    try:
        ap_if.config(essid=_essid, channel=_channel)
    except Exception as e:
        console_write(">>>>>>>>>>>>>>" + str(e))
    if ap_if.active() and str(ap_if.config('essid')) == str(_essid) and ap_if.config('channel') == _channel:
        is_success = True
    return is_success, ap_if.config('essid'), ap_if.config('channel'), ap_if.config('mac')

#########################################################
#                                                       #
#          AUTOMATIC NETWORK CONFIGURATION              #
#IF STA AVAIBLE, IF NOT AP MODE                         #
#########################################################
def auto_network_configuration(essid=None, pwd=None, timeout=50, ap_auto_disable=True, essid_force_connect=False, _essid=None, _pwd=None, _channel=11, sta_auto_disable=True):
    # GET DATA - STA
    if essid is None:
        essid = cfg.get("staessid")
    if pwd is None:
        pwd = cfg.get("stapwd")
    # GET DATA - AP
    if _essid is None:
        _essid = cfg.get("devfid")
    if _pwd is None:
        _pwd = cfg.get("appwd")

    # default connection type is STA
    isconnected, is_essid_exists = set_wifi(essid, pwd, timeout=timeout, ap_auto_disable=ap_auto_disable, essid_force_connect=essid_force_connect)
    console_write("STA======>" + str(isconnected) + "  - " + str(is_essid_exists))
    # if sta is not avaible, connect make AP for configuration
    if not (isconnected and is_essid_exists):
        console_write("STA MODE IS DISABLE - ESSID:{} or PWD:{} not valid".format(essid, pwd))
        ap_is_success, ap_essid, ap_channel, ap_config_mac = set_access_point(_essid=_essid, _pwd=_pwd, _channel=_channel, sta_auto_disable=sta_auto_disable)
        console_write("AP======>" + str(ap_is_success) + "  - " + str(ap_essid) + " - " + str(ap_channel) + " - " + str(ap_config_mac))
        cfg.put("nwmd", "AP")
    else:
        cfg.put("nwmd", "STA")

def network_wifi_scan():
    return [ i[0].decode("utf-8") for i in WLAN().scan() ]

#########################################################
#                                                       #
#               TEST AND DEMO FUNCTIONS                 #
#                                                       #
#########################################################
def network_demo():
    auto_network_configuration(essid="mywifi_essid", pwd="mywifi_passwd")

    '''
    # TEST CALLS
    #https://docs.micropython.org/en/latest/esp8266/library/network.html
    console_write("--TEST--> SET WIFI (STA)\n")
    console_write(set_wifi("mywifi_essid", "mywifi_passwd"))

    console_write("--TEST--> SET ACCESS POINT (AP)\n")
    console_write(set_access_point("NodeMcu", "guest"))

    console_write("--TEST--> GET WIFI RSSI INFO\n")
    console_write(wifi_rssi("mywifi_essid"))
    '''

    console_write("--TEST--> GET WIFI INFOS (after sta set)\n")
    wifi_info_dict = wifi_info()
    console_write(wifi_info_dict)

if __name__ == "__main__":
    network_demo()
