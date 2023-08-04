import LM_rgb
import LM_cct


def load_n_init(cache=None):
    """
    Unified rgb and cct module usage as one module
    """
    s1 = LM_rgb.load_n_init(cache)
    s2 = LM_cct.load_n_init(cache)
    return f'RGB: {s1}, CCT: {s2}'


def toggle(state=None, smooth=True):
    """
    Unified toggle function for rgb and cct control
    """
    rgb = LM_rgb.toggle(state, smooth)
    rgb_state = False if rgb['S'] == 0 else True
    cct = LM_cct.toggle(rgb_state, smooth)  # Set CCT value regarding rgb state (ensure it is in sync)
    rgb.update(cct)                         # Merge rgb and cct status
    return rgb


def brightness(percent=None, smooth=True, wake=True):
    """
    Unified brightness function for rgb and cct control
    """
    rgb = LM_rgb.brightness(percent, smooth, wake)
    cct = LM_cct.brightness(percent, smooth, wake)
    rgb.update(cct)                         # Merge rgb and cct status
    return rgb


def status(lmf=None):
    """
    Unified status function for rgb and cct modules
    """
    rgb = LM_rgb.status(lmf)
    cct = LM_cct.status(lmf)
    rgb.update(cct)                         # Merge rgb and cct status
    return rgb


def pinmap():
    """
    Unified pinmap function for rgb and cct modules
    """
    pins = LM_rgb.pinmap()
    pins.update(LM_cct.pinmap())
    return pins


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'load_n_init', 'toggle state smooth=True', 'brightness percent smooth=True wake=True',\
           'status', 'pinmap'
