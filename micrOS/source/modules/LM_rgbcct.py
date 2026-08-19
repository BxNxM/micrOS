import LM_rgb
import LM_cct
from Types import resolve


def __merge_status(rgb, cct):
    if not isinstance(rgb, dict) or not isinstance(cct, dict):
        return {'RGB': rgb, 'CCT': cct}
    rgb.pop('BR', None)
    cct.pop('BR', None)
    rgb.update(cct)                         # Merge rgb and cct status
    return rgb


def load(cache=None):
    """
    Unified rgb and cct module usage as one module
    """
    s1 = LM_rgb.load(cache)
    s2 = LM_cct.load(cache)
    return f'RGB: {s1}, CCT: {s2}'


def toggle(state=None, smooth=True):
    """
    Unified toggle function for rgb and cct control
    """
    rgb = LM_rgb.toggle(state, smooth)
    rgb_state = False if rgb['S'] == 0 else True
    cct = LM_cct.toggle(rgb_state, smooth)  # Set CCT value regarding rgb state (ensure it is in sync)
    return __merge_status(rgb, cct)


def status(lmf=None):
    """
    Unified status function for rgb and cct modules
    """
    rgb = LM_rgb.status(lmf)
    cct = LM_cct.status(lmf)
    return __merge_status(rgb, cct)


def pinmap():
    """
    Unified pinmap function for rgb and cct modules
    """
    pins = LM_rgb.pinmap()
    pins.update(LM_cct.pinmap())
    return pins


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('load',
                             'BUTTON toggle state=<True,False> smooth=True',
                             'STATUS status',
                             'pinmap'), widgets=widgets)
