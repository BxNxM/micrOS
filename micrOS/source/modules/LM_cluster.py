"""
micrOS ESPNow cluster module.
  -- STA/AP Channel sync            [OK]
  -- wifi settings sync             [OK]
  -- health (cluster availability)  [OK]
  -- cluster run <cmd>              [OK]
ShellCli (socket) extension (todo)
  -- health (cluster availability)
"""

from binascii import hexlify
from machine import soft_reset
from Config import cfgget, cfgput
from Network import _select_available_wifi_nw, ifconfig, WLAN, STA_IF, AP_IF
from Common import micro_task, exec_cmd, syslog
if cfgget("espnow"):
    from Espnow import ESPNowSS
    ESPNOW = ESPNowSS()
else:
    ESPNOW = None

class Cluster:
    CHANNEL = 6                     # Leader channel to align with
    ANCHOR_SSID_POSTFIX = "-mCSA"   # micrOS (Wifi) Channel Sync Anchor
    ANCHOR_ENABLED = False          # Anchor indicator
    REFRESH_MS = 20 * 60_000        # 20min - refresh channel sync period (AP mode)

#########################################################
#           CLUSTER - LOCAL EXECUTION "ON TARGET"       #
#########################################################

@micro_task("cluster", _wrap=True)
async def _reboot(tag:str):
    """
    Restart in the background
    (Enable function return before restart...)
    """
    with micro_task(tag) as my_task:
        await my_task.feed(5000)
        soft_reset()


def _update_wifi(ssid:str, pwd:str):
    """
    Local Config Setter - Add WiFi settings
    :param ssid: str - SSID
    :param pwd: str - Password
    """
    def _update_sta_config():
        nonlocal _ssid, _pwd
        essids = cfgget("staessid")
        passwords = cfgget("stapwd")
        if _ssid in essids:
            # [INFO] No password refresh is supported
            return f"Wifi already known: {ssid}"
        # Deserialize wifi settings from config file
        essids_list = essids.split(";")
        passwords_list = passwords.split(";")
        # Extend with new wifi settings
        essids_list.append(_ssid)
        passwords_list.append(_pwd)
        # Serialize back wifi settings to config file
        cfgput("staessid",";".join(essids_list))
        cfgput("stapwd", ";".join(passwords_list))
        # REBOOT
        _reboot()
        return "Soft reboot, apply wifi settings"

    if ';' in ssid or ';' in pwd:
        return "Unsupported character in ssid or pwd ;"
    # Check Wifi settings
    if cfgget("nwmd").upper() == "STA":
        # Check current wifi state
        if ifconfig()[0] == "STA":
            return "Device already connected to WiFi"
        # Validate wifi essid is available
        _ssid, _pwd = _select_available_wifi_nw(ssid, pwd)
        if _ssid is None:
            return f"Wifi SSID not available: {ssid}"
        return _update_sta_config()
    return "Wifi is in Access Point mode, skip sync"


def _run(cmd:str):
    state, out = exec_cmd(cmd.split(), secure=True)
    return f"[{'OK' if state else 'NOK'}] {out}"


@micro_task("cluster", _wrap=True)
async def _align_channel(tag:str, sta:STA_IF, ap:AP_IF):
    _initialized = False

    with micro_task(tag) as my_task:
        while True:
            my_task.out = "Sync in progress..."
            ch = Cluster.CHANNEL
            _refresh_ms = Cluster.REFRESH_MS
            for s, b, c, *_ in sta.scan():
                sta_name = (s.decode() if isinstance(s, bytes) else s)
                if sta_name.endswith(Cluster.ANCHOR_SSID_POSTFIX):
                    my_task.out = f"Anchor {sta_name} channel: {c} (refresh: {int(_refresh_ms/60_000)}min)"
                    ch = c
                    break

            if not _initialized or ch != Cluster.CHANNEL:
                Cluster.CHANNEL = ch
                if not sta.isconnected():
                    # ENABLE ESPNOW STA MAC ACCESS - AFTER THIS ALL DEVICES CAN REACH EACH OTHER ON STA MAC ADDRESS
                    try: sta.config(channel=ch)
                    except Exception as e:
                        my_task.out = f"STA Failed to set {ch} channel: {e}"
                # ensure AP advertises/operates on the same channel (important when STA not connected yet)
                try: ap.config(channel=ch)
                except Exception as e:
                    my_task.out = f"AP Failed to set {ch} channel: {e}"
                _initialized = True
            await my_task.feed(_refresh_ms)


@micro_task("cluster", _wrap=True)
async def _network(tag:str, anchor=False):
    """
    Support hybrid AP/STA ESPNow communication
    For ESPNow communication all device should use the same Wifi channel!
    - LEADER: STA*/AP mode - *channel is set by the router and can change
    - AP deices should use the same channel as ANCHOR (discovery by leader/anchor(STA) over AP anchor)
    - ESPNOW: STA mac addresses are stored on ANCHOR
    :param anchor: enable anchor mode (AP) for ESPNow channel synchronization
    """
    def _conf_ap_anchor():
        _ap = WLAN(AP_IF)
        if not _ap.active(): _ap.active(True)
        anchor_ssid = f"{cfgget('devfid')}{Cluster.ANCHOR_SSID_POSTFIX}"
        try:
            _ap.config(essid=anchor_ssid, password=cfgget("appwd"), authmode=3, max_clients=5)
            return True
        except Exception as e:
            syslog(f"[ERR] Anchor configuration failed: {e}")
        return False
    def _enable_sta():
        sta = WLAN(STA_IF)
        if not sta.active(): sta.active(True)
        return sta

    with micro_task(tag) as my_task:
        # CONFIGURE WIFI CHANNEL SYNC ROLES
        my_task.out = "Configure cluster network"
        micros_nw = ifconfig()[0]
        # MICROS in STA MODE
        if micros_nw == "STA":
            if anchor:
                # CREATE CHANNEL ANCHOR - AP channel is inherited from STA
                Cluster.ANCHOR_ENABLED = _conf_ap_anchor()
        else:
            # MICROS in AP MODE: CLUSTER FOLLOWER - WIFI CHANNEL SYNC WITH ANCHOR
            ap, sta = WLAN(AP_IF), _enable_sta()
            # Sync Channel with Cluster Anchor
            _align_channel(sta, ap)
            if anchor:
                # MICROS in AP MODE - RECONFIGURE AP NAME to match Anchor
                # EXPERIMENTAL FEATURE: Scans and Advertise the channel as well.
                Cluster.ANCHOR_ENABLED = _conf_ap_anchor()
        my_task.out = status()

#########################################################
#                 CLUSTER WIDE FEATURES                 #
#########################################################

def sync_wifi():
    """
    ESPNow Cluster Wifi Settings Sync for Station (STA) Connection Mode
    - Join devices to the same wifi network...
    """
    if ESPNOW is None:
        return "ESPNow is disabled"
    # Check current wifi state
    if ifconfig()[0] != "STA":
        return "No WiFi STA Connection: no verified settings to share"
    # [1] Get current wifi ssid and password
    _ssid, _pwd = _select_available_wifi_nw(cfgget("staessid"), cfgget("stapwd"))
    # [2] Send command: 'cluster _update_wifi "<ssid>" "<pwd>"'
    command = f"cluster _update_wifi '{_ssid}' '{_pwd}'"
    sync_tasks = ESPNOW.cluster_send(command)
    return sync_tasks


def run(cmd:str):
    """
    Run a command on the cluster
    :param cmd: str - command to run on the cluster
        Example: cmd='system heartbeat'
    """
    command = f"cluster _run '{cmd}'"
    sync_tasks = ESPNOW.cluster_send(command)
    return sync_tasks


def health():
    """
    Simple connection check
    - with default espnow-micros hello message
    """
    if ESPNOW is None:
        return "ESPNow is disabled"
    return ESPNOW.cluster_send("hello")


def members():
    """
    List all members in the cluster
    """
    if ESPNOW is None:
        return "ESPNow is disabled"
    return {hexlify(mac, ':').decode(): name for mac, name in ESPNOW.devices.items()}


def status():
    """
    Cluster setup status
    """
    nw_if = ifconfig()[0]
    cluster_settings = {"channel": Cluster.CHANNEL, "primary_nw": nw_if,
                        "anchor": Cluster.ANCHOR_ENABLED}
    if nw_if == "AP":
        cluster_settings["refresh"] = Cluster.REFRESH_MS
    return cluster_settings


def load(anchor:bool=False, refresh:int=None):
    """
    Enable ESPNow protocol 'cluster' module access
    :param anchor: create AP as Channel Anchor (Channel Leader Role)
    :param refresh: refresh channel sync period in minute (AP)
    """
    if ESPNOW is None:
        return "ESPNow is disabled"
    if refresh is not None:
        Cluster.REFRESH_MS = 60_000 if refresh < 1 else refresh * 60_000
    # Configure cluster network - after micrOS network setup
    _network(anchor)
    return f"Enable cluster module access"


def help(widgets=True):
    """
    [BETA]
    Show help for cluster commands
    """
    return ("load anchor=False refresh=20",
            "run 'command'",
            "sync_wifi",
            "health",
            "members",
            "status",
            "[Info] Get command results:\n\ttask show con.espnow.*")
