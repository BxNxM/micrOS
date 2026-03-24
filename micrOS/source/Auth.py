"""
micrOS Load Module Authentication/Access feature
    Designed by Marcell Ban aka BxNxM
"""
from Config import cfgget as __cfgget
PWD_KEY = "pwd"

def sudo(_f=None, *, _when_true=None):
    """
    Decorator for password-protected functions.
    Usage:
        @sudo
        def fn(...): ...
    Or:
        @sudo(_when_true=("flag", 0))
        def fn(flag, ...): ...

    :param _f: Internal use only. When decorator is used without parentheses.
        If None, the decorator is being configured, return a wrapper.
    :param _when_true: optional pwd check
      - _when_true=None: always require pwd
      - _when_true=(keyword:str, position:int): require pwd only when keyword/position is True
    Password check:
      - pwd check against node_config 'appwd' value
    """

    def deco(f):
        wt_kw = wt_idx = None
        if _when_true is not None:
            wt_kw, wt_idx = _when_true

        def w(*a, **k):
            # Decide if password is required
            require = True
            if wt_kw is not None or wt_idx is not None:
                require = False
                # Keyword-based condition
                if wt_kw is not None and k.get(wt_kw, False):
                    require = True
                # Positional-based condition
                if wt_idx is not None and 0 <= wt_idx < len(a):
                    if a[wt_idx]:
                        require = True

            # Password check
            if require and k.get(PWD_KEY) != __cfgget("appwd"):
                raise Exception(f"Access denied, wrong password ({PWD_KEY})")
            # Remove password before calling function
            k.pop(PWD_KEY, None)
            return f(*a, **k)
        return w
    return deco if _f is None else deco(_f)


def resolve_secret(commands:str):
    """
    Resolve secret: $pwd in boothook
    """
    placeholder = f"${PWD_KEY}"
    if placeholder in commands:
        commands = commands.replace(placeholder, f"'{__cfgget("appwd")}'")
    return commands
