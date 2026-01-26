"""
Web backend loader
    - Dynamic application dashboard
    - Fileserver
"""

from Common import web_endpoint


def load(dashboard=True, fileserver=False, fsdir=None):
    """
    Centralized Web Backend Services Loader
    - Dynamic application dashboard
    - Fileserver
    :param dashboard: bool - enable*/disable application dashboard
    :param fileserver: bool - enable/disable* fileserver
    :param fsdir: str - set custom fileserver shared folder name
    """
    endpoints = []
    if dashboard:
        web_endpoint('dashboard', 'dashboard.html')
        endpoints.append("Dashboard initialized, endpoint: /dashboard")
    if fileserver:
        import LM_fileserver
        endpoints.append(LM_fileserver.load(web_data_dir=fsdir))
    return endpoints


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return ('load dashboard=True fileserver=False fsdir=None',
            'help')
