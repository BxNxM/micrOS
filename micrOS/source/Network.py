"""
Module is responsible for network configuration
dedicated to micrOS framework.
- STA / STA
- static IP configuration
- NTP clock setup in case of STA
- generate UID based on mac address
- network status expose to config

Designed by Marcell Ban aka BxNxM

https://docs.micropython.org/en/latest/library/network.html
"""
#################################################################
#                           IMPORTS                             #
#################################################################
from utime import sleep_ms
from binascii import hexlify
from network import AP_IF, STA_IF, WLAN
from machine import unique_id
from ConfigHandler import cfgget, cfgput
from Debug import console_write, errlog_add

NW_IF = None

#################################################################
#                 NW INTERFACE STATUS FUNCTIONS                 #
#################################################################


def ifconfig():
    """
    :return: network mode (AP/STA), ifconfig tuple
    """
    if NW_IF is None:
        return '', ("0.0.0.0", "0.0.0.0", "0.0.0.0", "0.0.0.0")
    nw_mode = 'STA'
    if_tuple = NW_IF.ifconfig()
    if if_tuple[0] == if_tuple[2]:
        nw_mode = 'AP'
    return nw_mode, if_tuple

#################################################################
#                   GET DEVICE UID BY MAC ADDRESS               #
#################################################################


def set_dev_uid():
    try:
        cfgput('hwuid', f'micr{hexlify(unique_id()).decode("utf-8")}OS')
    except Exception as e:
        errlog_add(f"[ERR] set_dev_uid error: {e}")


def get_mac():
    return hexlify(WLAN().config('mac'), ':').decode()

#################################################################
#                       SET WIFI STA MODE                       #
#################################################################


def __select_available_wifi_nw(sta_if, raw_essid, raw_pwd):
    """
    raw_essid: essid parameter, in case of multiple values separator is ;
    raw_pwd: essid pwd parameter,  in case of multiple values separator is ;
    return detected essid with corresponding password
    """
    for idx, essid in enumerate(raw_essid.split(';')):
        essid = essid.strip()
        # Scan wifi network - retry workaround
        for _ in range(0, 2):
            if essid in (wifispot[0].decode('utf-8') for wifispot in sta_if.scan()):
                console_write(f'\t| - [NW: STA] ESSID WAS FOUND: {essid}')
                try:
                    return essid, str(raw_pwd.split(';')[idx]).strip()
                except Exception as e:
                    console_write(f'\t| - [NW: STA] wifi stapwd config error: {e}')
                    errlog_add(f'[ERR][SET STA] stapwd config error: {e}')
            sleep_ms(400)
    return None, ''


def set_wifi(essid, pwd, timeout=60):
    global NW_IF
    console_write(f'[NW: STA] SET WIFI STA NW {essid}')

    # Disable AP mode
    ap_if = WLAN(AP_IF)
    if ap_if.active():
        ap_if.active(False)
    del ap_if

    # Set STA and Connect
    sta_if = WLAN(STA_IF)
    sta_if.active(True)
    # Handle rsp2-w limitation (try)
    try:
        # Set custom DHCP hostname for dhcp name resolve
        sta_if.config(dhcp_hostname=cfgget('devfid'))
    except Exception as e:
        console_write(f"dhcp_hostname conf error: {e}")
    # Check are we already connected
    if sta_if.isconnected():
        console_write(f"\t| [NW: STA] ALREADY CONNECTED TO {essid}")
    else:
        # Multiple essid and pwd handling with retry mechanism
        essid, pwd = __select_available_wifi_nw(sta_if, essid, pwd)

        # Connect to the located wifi network
        if essid is not None:
            console_write(f'\t| [NW: STA] CONNECT TO NETWORK {essid}')
            # connect to network
            sta_if.connect(essid, pwd)
            # wait for connection, with timeout set
            while not sta_if.isconnected() and timeout > 0:
                console_write(f"\t| [NW: STA] Waiting for connection... {timeout} sec")
                timeout -= 1
                sleep_ms(500)
            # Set static IP - here because some data comes from connection. (subnet, etc.)
            if sta_if.isconnected() and __set_wifi_dev_static_ip(sta_if):
                sta_if.disconnect()
                del sta_if
                return set_wifi(essid, pwd)
        else:
            console_write(f"\t| [NW: STA] Wifi network was NOT found: {essid}")
            return False
        console_write(f"\t|\t| [NW: STA] network config: {str(sta_if.ifconfig())}")
        console_write(f"\t|\t| [NW: STA] CONNECTED: {str(sta_if.isconnected())}")

    # Store STA IP (make it static ip)
    cfgput("devip", str(sta_if.ifconfig()[0]))
    set_dev_uid()
    NW_IF = sta_if
    return sta_if.isconnected()


def __set_wifi_dev_static_ip(sta_if):
    console_write("[NW: STA] Set device static IP.")
    stored_ip = cfgget('devip')
    if 'n/a' not in stored_ip.lower() and '.' in stored_ip:
        conn_ips = list(sta_if.ifconfig())
        # Check ip type before change, conn_ip structure: 10.0.1.X
        if conn_ips[0] != stored_ip and conn_ips[-1].split('.')[0:3] == stored_ip.split('.')[0:3]:
            console_write(f"\t| [NW: STA] micrOS dev. StaticIP request: {stored_ip}")
            conn_ips[0] = stored_ip
            try:
                # IP address, subnet mask, gateway and DNS server
                sta_if.ifconfig(tuple(conn_ips))
                return True     # was reconfigured
            except Exception as e:
                console_write(f"\t\t| [NW: STA] StaticIP conf. failed: {e}")
                errlog_add(f"__set_wifi_dev_static_ip error: {e}")
        else:
            console_write(f"[NW: STA][SKIP] StaticIP conf.: {stored_ip} ? {conn_ips[0]}")
    else:
        console_write(f"[NW: STA] IP was not stored: {stored_ip}")
    return False   # was not reconfigured


#################################################################
#                    SET WIFI ACCESS POINT MODE                 #
#################################################################


def set_access_point(_essid, _pwd, _authmode=3):
    global NW_IF
    console_write(f"[NW: AP] SET AP MODE: {_essid} - {_pwd} - auth mode: {_authmode} (if possible)")

    sta_if = WLAN(STA_IF)
    if sta_if.isconnected():
        sta_if.active(False)

    ap_if = WLAN(AP_IF)
    ap_if.active(True)
    # Set WiFi access point name (formally known as ESSID) and WiFi authmode (3): WPA2-PSK
    try:
        # Config #1 (esp)
        console_write("[NW: AP] Configure")
        ap_if.config(essid=_essid, password=_pwd, authmode=_authmode, max_clients=5)
    except Exception as e1:
        # Correction because rp2-w network interface limitation (parameter mismatch)
        console_write(f"[NW: AP] Config Error: {e1}")
        try:
            console_write("|- Simplified config...")
            # Config #2 (rp2-w)???
            ap_if.config(essid=_essid, password=_pwd)
        except Exception as e2:
            console_write(f"|- [NW: AP] Config Error: {e2}")
            errlog_add(f"[ERR] set_access_point error: {e2}")
    if not (ap_if.active() and str(ap_if.config('essid')) == str(_essid)):
        errlog_add("[ERR][SET AP] config error")
    console_write(f"\t|\t| [NW: AP] network config: {str(ap_if.ifconfig())}")
    set_dev_uid()
    NW_IF = ap_if
    return ap_if.active()

#################################################################
#              AUTOMATIC NETWORK CONFIGURATION                  #
#              IF STA AVAILABLE, IF NOT AP MODE                 #
#################################################################


def auto_nw_config():
    # Retry mechanism - create some connection... prio.: STA > AP
    nwmd = cfgget('nwmd')
    for _ in range(0, 3):
        # nwmd: default or STA
        if nwmd is None or "AP" not in nwmd.upper():
            # SET WIFI (STA) MODE
            state = set_wifi(cfgget("staessid"), cfgget("stapwd"))
            if state:
                # STA mode successfully  configures
                return 'STA'
        # SET AP MODE - chack later if AP (additional ble interface case)
        state = set_access_point(cfgget("devfid"), cfgget("appwd"))
        if state:
            # AP mode successfully  configures
            return 'AP'
    return 'Unknown'


def sta_high_avail():
    """
    Check and repair STA network mode
    - IF STA not connected and wifi network available, then auto reconnect
    """
    # [CHECK 1] if nwmd STA and not connected ---> repair action
    sta_if = WLAN(STA_IF)
    if cfgget('nwmd') == 'STA' and not sta_if.isconnected():
        raw_essid = cfgget("staessid")
        wifi_avail = False
        # [CHECK 2] check known network is available
        for idx, essid in enumerate(raw_essid.split(';')):
            essid = essid.strip()
            # Scan wifi network - retry workaround
            for _ in range(0, 2):
                if essid in (wifispot[0].decode('utf-8') for wifispot in sta_if.scan()):
                    wifi_avail = True

        ap_if = WLAN(AP_IF)
        # [CHECK 3] if known wifi available (REPAIR) or device not in AP mode ---> (FALLBACK) temporary direct access
        if wifi_avail or not ap_if.active():
            # ACTION: Restart micrOS node (boot phase automatically detects nw mode)
            from machine import reset
            reset()
        return f'{cfgget("nwmd")} mode NOK, wifi avail: {wifi_avail}'
    return f'{cfgget("nwmd")} mode, OK'
