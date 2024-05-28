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
from json import dumps
########################################################
#                 HELP TUPLE RESOLVER                  #
########################################################
__TEMPLATE = {'type': 'n/a', 'lm_call': ''}
__RANGE_100 = {'range': (0, 100, 2)}
__RANGE_255 = {'range': (0, 255, 2)}
__RANGE_OPTS = {'range': ("True", "False")}


BUTTON = __TEMPLATE | {'type': 'button'}                                    # Mandatory func params: n/a
TOGGLE = __TEMPLATE | {'type': 'toggle'} | __RANGE_OPTS                     # Mandatory func params: state
SLIDER = __TEMPLATE | {'type': 'slider'} | __RANGE_100                      # Mandatory func params: br
TEXTBOX = __TEMPLATE | {'type': 'textbox','repeat': False, 'period_s': 3}   # Mandatory func params: n/a
COLOR = __TEMPLATE | {'type': 'color'} | __RANGE_255                        # Mandatory func params: r, g, b
WHITE = __TEMPLATE | {'type': 'white'} | __RANGE_255                        # Mandatory func params: wc, ww


def _placeholder(var, value, type_dict):
    def _is_int(data):
        try:
            int(data)
            return True
        except:
            return False

    new_range = None
    if value.startswith('<') and value.endswith('>'):
        if '-' in value:
            _range = value[1:-1].split('-')
            # Range param int check
            if len([r for r in _range if not _is_int(r)]) == 0:
                # Get custom range values
                _min, _max, _step = (_range[0], _range[1], _range[2]) if len(_range) > 2 else (_range[0], _range[1], None)
                if _step is None:
                    _step = type_dict['range'][2]
                new_range = (int(_min), int(_max), int(_step))
                #print(f"[i] Range overwrite[{var}]: {_range}")
                return f"{var}=:range:", new_range
            # Ignore param
            return "", new_range
    # Keep param value
    return f"{var}={value}", new_range


def _generate(type_dict, help_msg):
    func = help_msg.split()[1]
    params = help_msg.split()[2:] if len(help_msg.split()) > 2 else []
    valid_params = []
    for p in params:
        if '=' in p:
            var, value = p.split("=")
            p, new_range = _placeholder(var, value, type_dict)
            if new_range is not None:
                type_dict['range'] = new_range
        else:
            # Empty param fallback
            p = f'{p}=:range:'
        valid_params.append(p)
    type_dict['lm_call'] = f"{func} " + " ".join(valid_params)
    return dumps(type_dict)

def resolve(help_data, widgets=False):
    help_msg = []
    for msg in help_data:
        tag = msg.split()[0].strip()
        # TYPE DECORATION detect in help strings
        if tag.isupper():
            resolved_tag = _resolve_key(tag)
            if resolved_tag == tag:
                if widgets:
                    continue                                    # Invalid tag in widget mode
                help_msg.append(msg.replace(tag, '').strip())   # Invalid tag (OK) in human readable mode
                continue
            # Create json string type + extract widgets from help message
            help_msg.append(_generate(resolved_tag, msg))
        elif not widgets:
            # Human readable mode (non decorated functions)
            help_msg.append(msg)
    return tuple(help_msg)

def _resolve_key(key):
    try:
        type_info = eval(f'{key}')
    except NameError:
        return key
    return type_info
