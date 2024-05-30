from Common import web_endpoint, syslog

ENDPOINT_INITED = False

def load():
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
    web_endpoint('dashboard', _dashboard_clb)
    return 'Endpoint created: /dashboard'


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'load', 'create_dashboard', 'help'