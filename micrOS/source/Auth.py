"""
micrOS Load Module Authentication features
    Designed by Marcell Ban aka BxNxM
"""
from Config import cfgget as __cfgget
PWD_KEY = "pwd"

def sudo(_f=None, *, _force_only=(False, -1)):
    """
    Decorator for password-protected functions.
    - _force_only=(False, _): always require pwd
    - _force_only=(True, idx): require pwd only when force is True
      (force can be passed as kw: force=..., or positionally at args[idx])
    - pwd is checked against node_config appwd value, and is not passed to the function
    """
    def deco(f):
        fo, idx = _force_only
        def w(*a, **k):
            force = k.get("force", None)
            if force is None and fo and 0 <= idx < len(a):
                force = a[idx]
            if (not fo or force) and k.get(PWD_KEY) != __cfgget("appwd"):
                raise Exception(f"Access denied, wrong password ({PWD_KEY})")
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
