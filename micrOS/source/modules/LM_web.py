"""
Web backend loader
    - Dynamic application dashboard
    - Fileserver
"""

from Common import web_endpoint, web_mounts


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


def _cfg_get_clb():
    """
    Get system config - beta - example
    """
    example_load = "system clock; rgb load"
    example_cron = "0:16:30:0!rgb toggle"
    example_irq = "rgb toggle"
    example_pins = "map-name; pin-name:0"
    return {"network": {"ssid": ["wifi-name",],                                                 # staessid
                        "password": ["wifi-password",],                                         # stapwd
                        "webui": False,                                                         # webui
                        "espnow": False,                                                        # espnow
                        "mode": "STA/AP"},                                                      # nwmd
            "tasks": {"boot": example_load,                                                     # boothook
                      "cron": False, "cron-tasks": example_cron,                                # cron, crontasks
                      "timirq": False, "timirq-tasks": example_irq, "timirq-seq": 3000,         # timirq, timirqcbf, timirqseq
                      "irq1": False, "irq1-tasks": example_irq, "irq1-trig": "down/up/both",    # irq1, irq1_cbf, irq1_trig
                      "irq2": False, "irq2-tasks": example_irq, "irq2-trig": "down/up/both",
                      "irq3": False, "irq3-tasks": example_irq, "irq3-trig": "down/up/both",
                      "irq4": False, "irq4-tasks": example_irq, "irq4-trig": "down/up/both"},
            "system": {"device-name": "node01",                                                 # devfid
                       "password": "system-and-ap-and-webrepl-password",                        # appwd
                       "custom-pins": example_pins                                              # cstmpmap
                       }
            }

def _cfg_set_clb(delta=None):
    """
    Set system config delta - beta - example
    """
    pass


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return ('load dashboard=True fileserver=False fsdir=None fs_explore=False',
            'help')
