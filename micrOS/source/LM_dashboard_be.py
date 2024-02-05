from Common import rest_endpoint, syslog
from sys import modules

WIDGETS={}

def load_n_init():
    return create_dashboard()


def _dashboard_clb():
    try:
        with open('dashboard.html', 'r') as html:
            html_content = html.read()
        return 'text/html', html_content
    except Exception as e:
        syslog(f"[ERR] dashboard_be: {e}")
        html_content = None
    return 'text/plain', f'html_content error: {html_content}'


def create_dashboard():
    """
    Create dashboard endpoint
    """
    rest_endpoint('dashboard', _dashboard_clb)
    return 'Endpoint created: /dashboard'


def app_list():
    """
    API HELPER: return loaded application modules
    """
    app_list = [m.strip().replace('LM_', '') for m in modules if m.startswith('LM_')]
    return list(app_list)


def custom_commands(widget=None):
    """
    :param widget: {'OV2640/settings/saturation=': 'slider'}
    API HELPER: return {'rest/command': <type>}
    <type>: slider, button, box, h1, h2, p, etc...
    """
    global WIDGETS
    if isinstance(widget, dict):
        WIDGETS.update(widget)
    if widget is None:
        return WIDGETS


def help():
    return 'load_n_init', 'create_dashboard', 'app_list', 'custom_commands', 'help'