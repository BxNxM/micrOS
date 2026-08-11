"""
Web backend loader
    - Dynamic application dashboard
    - Fileserver
"""

from json import dumps, loads

from Common import web_endpoint, web_mounts
from Config import cfgget, cfgput
from Auth import sudo

_CFG_HIDE = ("hwuid", "guimeta", "socport", "version", "auth", "soctout")


def load(dashboard=True, fileserver:bool=False, fs_explore:bool=False, config=True):
    """
    Centralized Web Backend Services Loader
    - Dynamic application dashboard
    - Fileserver
    :param dashboard:  bool - enable*/disable application dashboard
    :param fileserver: bool - enable/disable* fileserver
    :param fs_explore: bool - enable/disable* all shared web mounts: modules, data
    :param config: bool     - enable*/disable micrOS web config with auth
    """
    endpoints = []
    if dashboard:
        web_endpoint('dashboard', 'dashboard.html')
        endpoints.append("Dashboard initialized, endpoint: /dashboard")
    if fileserver:
        import LM_fileserver
        endpoints.append(LM_fileserver.load())
        endpoints.append(web_mounts(fs_explore, fs_explore, fs_explore))
    if config:
        endpoints.append(enable_config())
    return endpoints


def enable_config():
    """
    Enable web configuration option
    """
    web_endpoint("config", _cfg_get_clb)
    web_endpoint("config", _cfg_set_clb, "POST")
    web_endpoint("config/ui", 'config.html')
    return "Auth protected endpoint: /config GET|POST"


def _cfg_json(data):
    return "application/json", dumps(data)


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
        print('Received config update request:', incoming_data)
        failed_keys = []
        for k, v in incoming_data.items():
            try:
                if k == 'devfid' and not str(v).strip():
                    raise Exception("Device name cannot be empty")
                if k == 'crontasks' and isinstance(v, str) and not v.strip():
                    v = 'n/a'
                state = cfgput(k, v)
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


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return ('load dashboard=True fileserver=False fs_explore=False config=True',
            'enable_config',
            'help')
