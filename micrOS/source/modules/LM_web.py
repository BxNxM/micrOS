"""
Web backend loader
    - Dynamic application dashboard
    - Fileserver
"""

from json import dumps

from Common import web_endpoint, web_mounts
from Config import cfgget
from Auth import sudo

_CFG_HIDE = ("webui", "hwuid", "guimeta", "socport", "version", "auth", "soctout")


def load(dashboard=True, fileserver:bool=False, fs_explore:bool=False):
    """
    Centralized Web Backend Services Loader
    - Dynamic application dashboard
    - Fileserver
    :param dashboard:  bool - enable*/disable application dashboard
    :param fileserver: bool - enable/disable* fileserver
    :param fs_explore: bool - enable all shared web mounts: modules, data
    """
    endpoints = []
    if dashboard:
        web_endpoint('dashboard', 'dashboard.html')
        endpoints.append("Dashboard initialized, endpoint: /dashboard")
    if fileserver:
        import LM_fileserver
        endpoints.append(LM_fileserver.load())
        endpoints.append(web_mounts(fs_explore, fs_explore, fs_explore))
    return endpoints


@sudo
def enable_config():
    """
    Enable web configuration option
    """
    web_endpoint("config", _cfg_get_clb)
    web_endpoint("config", _cfg_set_clb, "POST")
    web_endpoint("config/ui", 'config.html')
    return "Endpoints: /config and /config/ui"


def _cfg_json(data):
    return "application/json", dumps(data)


def _cfg_get_clb(*_):
    """
    Get system config
    """
    return _cfg_json({k: v for k, v in cfgget().items() if k not in _CFG_HIDE})


def _cfg_set_clb(*_):
    """
    Set system config delta - not implemented yet
    """
    return _cfg_json({"state": False, "result": "Config set is not implemented"})


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return ('load dashboard=True fileserver=False fs_explore=False',
            'enable_config',
            'help')
