"""
micrOS ESPNow cluster module.
  -- wifi settings sync             [OK]
  -- health (cluster availability)
ShellCli (socket) extension (todo)
  -- health (cluster availability)
"""

from machine import soft_reset
from Config import cfgget, cfgput
from Network import _select_available_wifi_nw, ifconfig
from Common import micro_task, exec_cmd
if cfgget("espnow"):
    from Espnow import ESPNowSS
    ESPNOW = ESPNowSS()
else:
    ESPNOW = None


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
        my_task.feed(3000)
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


def load():
    """
    Enable ESPNow protocol 'cluster' module access
    """
    return "Enable cluster module access"


def help(widgets=True):
    """
    [BETA]
    Show help for cluster commands
    """
    return ("load",
            "sync_wifi",
            "health",
            "run 'command'"
            "[Info] Get command results: task show con.espnow.*")
