"""
OBSOLETED Web backend loader
"""

from LM_web import load as web_load


def load(*args, **kwargs):
    """
    OBSOLETED: use web load instead
    """
    return create_dashboard(*args, **kwargs)


def create_dashboard(*args, **kwargs):
    """
    OBSOLETED: use web load instead
    """
    return web_load(*args, **kwargs)


def help(widgets=False):
    """
    OBSOLETED: use web load instead
    """
    return 'load', 'create_dashboard', 'help'
