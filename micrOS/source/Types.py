"""
micrOS Frontend element types - 'This is the frontend perspective of micrOS functions'
- Can be attached for Load Module functions in module help tuple

USAGE:
    <TAG> function params*
    BUTTON toggle

    <range> int
    SLIDER brightness br
    SLIDER brightness br=<0-100>
    SLIDER brightness br=<0-100-5>
"""
from json import dumps, loads
from Debug import syslog

########################################################
#                 HELP TUPLE RESOLVER                  #
########################################################

__TEMPLATE = {'type': 'n/a', 'lm_call': ''}
__RANGE_100 = {'range': (0, 100, 2)}
__RANGE_255 = {'range': (0, 255, 2)}
__OPTIONS = {'options': ("None",)}

# Widget Types
BUTTON = lambda: __TEMPLATE | {'type': 'button'} | __OPTIONS
SLIDER = lambda: __TEMPLATE | {'type': 'slider'} | __RANGE_100
TEXTBOX = lambda: __TEMPLATE | {'type': 'textbox', 'refresh': 10000}
COLOR = lambda: __TEMPLATE | {'type': 'color'} | __RANGE_255
WHITE = lambda: __TEMPLATE | {'type': 'white'} | __RANGE_255
JOYSTICK = lambda: __TEMPLATE | {'type': 'joystick'} | __RANGE_100


########################################################
#                       FUNCTIONS                      #
########################################################

def _placeholder(var, value, type_dict):
    def _is_int(data):
        try:
            int(data)
            return True
        except ValueError:
            return False

    if value.startswith('<') and value.endswith('>'):
        if '-' in value:
            _range = value[1:-1].split('-')
            if all(_is_int(r) for r in _range):
                _min, _max = int(_range[0]), int(_range[1])
                _step = int(_range[2]) if len(_range) > 2 else type_dict['range'][2]
                return f"{var}=:range:", (_min, _max, _step), 'range'
            return "", None, None
        if ',' in value:
            _opts = tuple(value[1:-1].split(','))
            return f"{var}=:options:", _opts, 'options'
    return f"{var}={value}", None, None


def _generate(type_dict, help_msg):
    parts = help_msg.split()
    func, params = parts[1], parts[2:] if len(parts) > 2 else []
    valid_params, overwrite = [], {}
    for p in params:
        if '=' in p:
            var, value = p.split("=")
            param_str, values, value_type = _placeholder(var, value, type_dict)
            if value_type:
                overwrite[value_type] = values
            valid_params.append(param_str)
        else:
            if p.startswith("&"):
                # Handle special use case - task postfix
                valid_params.append(p)
            else:
                param_str = f'{p}=:{"range" if "range" in type_dict else "options"}:'
                valid_params.append(param_str)
    type_dict['lm_call'] = f"{func} {' '.join(valid_params)}"
    return dumps(type_dict | overwrite)


def _extract_tag_and_overrides(msg):
    """
    Example:
      "TEXTBOX{'refresh': 5000} measure ntfy=False"
    OR with default refresh value:
      "TEXTBOX measure ntfy=False"
    return:
      tag                   -> "TEXTBOX"
      overrides(optional)   -> {'refresh': 5000}
      cmd                   -> "measure ntfy=False"
    """
    msg = msg.strip()
    if not msg:
        return "", {}, ""
    tag_end = len(msg)
    for i, c in enumerate(msg):
        if c in " {":
            tag_end = i
            break
    tag = msg[:tag_end]
    cmd = msg[tag_end:].lstrip()
    overrides = {}
    if tag.isupper() and cmd.startswith('{'):
        i = cmd.find('}')
        if i >= 0:
            try:
                overrides = loads('{' + cmd[1:i].replace("'", '"') + '}')
            except Exception as e:
                syslog(f"[ERR] Types tag overrides: {e}")
            cmd = cmd[i + 1:].lstrip()
    return tag, overrides, cmd


def resolve(help_data, widgets=False):
    help_msg = []
    for msg in help_data:
        tag, overrides, cmd = _extract_tag_and_overrides(msg)
        if tag and tag.isupper():
            # TAG exists in help message
            if widgets:
                # Format output as widget - machine-readable
                factory = globals().get(tag, None)
                resolved_tag = factory() if callable(factory) else factory
                if isinstance(resolved_tag, dict) and overrides:
                    # Apply inline widget-only overrides, e.g. TEXTBOX{'refresh': 5000}
                    resolved_tag.update(overrides)
                try:
                    # Build a clean message for _generate, without inline {...}
                    cleaned_msg = (tag + ' ' + cmd).strip()
                    # Generate JSON output with TAG
                    help_msg.append(_generate(resolved_tag, cleaned_msg))
                except Exception as e:
                    syslog(f"[ERR] resolve {tag} help msg: {e}")
                continue
            # Widgets OFF - TAG exists - remove TAG from output
            help_msg.append(cmd.strip())
        elif not widgets:
            # No TAG - Widgets OFF output
            help_msg.append(msg)
    return tuple(help_msg)
