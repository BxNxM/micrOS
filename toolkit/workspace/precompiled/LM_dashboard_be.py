from Common import rest_endpoint, syslog
from sys import modules

WIDGETS={}
ENDPOINT_INITED = False

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
    global ENDPOINT_INITED
    ENDPOINT_INITED = True
    rest_endpoint('dashboard', _dashboard_clb)
    return 'Endpoint created: /dashboard'


def app_list():
    """
    API HELPER: return loaded application modules
    """
    app_list = [m.strip().replace('LM_', '') for m in modules if m.startswith('LM_')]
    return list(app_list)


def widget_list():
    """
    API HELPER: return custom widgets dict
    """
    return WIDGETS



def widget_add(widget=None):
    """
    :param widget: {'OV2640': {'settings/saturation=': 'slider',
                               'settings/brightness=': <type>}}
    <type>: 'slider', 'button', 'box', 'h1', 'h2', 'p', etc...
    """
    global WIDGETS
    if not ENDPOINT_INITED:
        load_n_init()           # auto-enable dashboard endpoint
    if isinstance(widget, dict):
        WIDGETS.update(widget)


def help():
    return 'load_n_init', 'create_dashboard', 'app_list', 'widget_list', 'widget_add', 'help'