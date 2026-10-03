"""
Web backend loader
    - Dynamic application dashboard
    - Fileserver
"""

from json import dumps, loads, dump as conf_dump, load as conf_load

from Common import web_endpoint, conf_dir, syslog
from Config import cfgget, cfgput
from Auth import sudo


def load(dashboard:bool=None, fileserver:bool=None, fs_explore:bool=None, config:bool=None):
    """
    Centralized Web Backend Services Loader
    - Dynamic application dashboard
    - Fileserver
    :param dashboard:  bool - enable*/disable application dashboard
    :param fileserver: bool - enable/disable* fileserver
    :param fs_explore: bool - enable/disable* all shared web mounts: modules, data
    :param config:     bool - enable*/disable micrOS web config with auth
    """
    msg = []
    wsc = _web_apps("r")

    dashboard = wsc["dashboard"] if dashboard is None else dashboard
    if dashboard:
        web_endpoint('dashboard', 'dashboard.html')
        msg.append("Dashboard initialized, endpoint: /dashboard")
    fileserver = wsc["fileserver"] if fileserver is None else fileserver
    fs_explore = wsc["fs_explore"] if fs_explore is None else fs_explore
    if fileserver:
        import LM_fileserver
        msg.append(LM_fileserver.load())
        msg.append(LM_fileserver.extend_mounts(modules=fs_explore, data=fs_explore, logs=fs_explore))
    config = wsc["config"] if config is None else config
    if config:
        msg.append(enable_config())

    _web_apps('s', {"dashboard": dashboard,
                                        "fileserver": fileserver, "fs_explore": fs_explore,
                                        "config": config})
    return msg


def _web_apps(mode, conf=None):
    """
    :param mode (str): s - save or r - read
    """
    if mode == "s":
        if conf is None:
            return False
        # Save config
        try:
            with open(conf_dir("webapps.json"), 'w') as f:
                conf_dump(conf, f)
            return True
        except Exception as e:
            syslog(f"[WARN] Web app conf save: {e}")
            return False
    # Load config (with fallback)
    cfg = {"dashboard": True, "fileserver": False, "fs_explore": False, "config": True}
    try:
        with open(conf_dir("webapps.json"), 'r') as f:
            cfg.update(conf_load(f))
    except Exception as e:
        syslog(f"[WARN] Web app conf load: {e}")
    return cfg


def status():
    """
    Web services status: dashboard, fileserver, fs_explore, config
    """
    return _web_apps('r')

######################## System Config ######################
_CFG_HIDE = ("hwuid", "guimeta", "socport", "version", "auth", "soctout")

def enable_config():
    """
    Enable web configuration option
    """
    web_endpoint("config", 'config.html')
    web_endpoint("config/api", _cfg_get_clb)
    web_endpoint("config/api", _cfg_set_clb, "POST")
    web_endpoint("config/packregs", _cfg_packregs_clb)
    web_endpoint("config/reboot", _reboot_clb, "POST")
    return "Config endpoints: /config GET, /config/api GET|POST (protected), /config/packregs GET, /config/reboot POST (protected)"


def _cfg_json(data):
    return "application/json", dumps(data)


def _cfg_packregs_clb(*_):
    """Get package registry JSON links for the config frontend."""
    return _cfg_json(["https://raw.githubusercontent.com/BxNxM/micrOSPackages/main/registry.json"])


@sudo
def _cfg_get_clb(*_):
    """
    Get system config
    """
    return _cfg_json({k: v for k, v in cfgget().items() if k not in _CFG_HIDE})


@sudo
def _cfg_set_clb(_, body):
    """
    Set system config delta
    """
    try:
        incoming_data = loads(body.decode('utf-8'))
        print('Received config update keys:', tuple(incoming_data))
        failed_keys = []
        for k, v in incoming_data.items():
            try:
                if isinstance(v, str) and not v.strip():
                    if k == 'devfid':
                        raise Exception("Device name cannot be empty")
                    v = 'n/a'
                state = cfgput(k, v, type_check=True)
            except Exception as e:
                state = False
                k = f"{k}: {e}"
            if not state:
                failed_keys.append(k)
        if failed_keys:
            return _cfg_json({
                "state": False,
                "result": "Config update failed",
                "failed": failed_keys
            })
        return _cfg_json({"state": True, "result": "Config updated"})
    except Exception as e:
        return _cfg_json({"state": False, "result": str(e)})


@sudo
def _reboot_clb(*_):
    """
    Soft reboot system from web endpoint
    """
    from Common import micro_task
    from machine import soft_reset

    @micro_task("web.reboot", _wrap=True)
    async def _soft_reboot(tag):
        with micro_task(tag) as my_task:
            await my_task.feed(1000)
            soft_reset()

    return _cfg_json({"state": bool(_soft_reboot()), "result": "Soft reboot scheduled"})

#############################################################


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return ('load dashboard=True fileserver=False fs_explore=False config=True',
            'enable_config',
            'status',
            'help')
