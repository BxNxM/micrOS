"""
Enable web endpoint dashboard.html -> dashboard
"""

from Common import web_endpoint

def load():
    return create_dashboard()


def create_dashboard():
    """
    Create dashboard endpoint
    """
    web_endpoint('dashboard', 'dashboard.html')
    return 'Endpoint created: /dashboard'


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'load', 'create_dashboard', 'help'
