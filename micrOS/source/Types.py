"""
micrOS Frontend element types
- Can be attached for Load Module functions in module help tuple

USAGE:
    <TAG> function params*
    BUTTON toggle

    <range> int
    SLIDER brightness br
    SLIDER brightness br=<0-100>
    SLIDER brightness br=<0-100-5>
"""

########################################################
#                 HELP TUPLE RESOLVER                  #
########################################################
__TEMPLATE = {'type': 'n/a', 'lm_call': ''}
__RANGE_100 = {'range': (0, 100, 2)}
__RANGE_255 = {'range': (0, 255, 2)}


BUTTON = __TEMPLATE | {'type': 'button'}
SLIDER = __TEMPLATE | {'type': 'slider'} | __RANGE_100
TEXTBOX = __TEMPLATE | {'type': 'textbox','repeat': False, 'period_s': 3}
COLOR = __TEMPLATE | {'type': 'color'} | __RANGE_255
WHITE = __TEMPLATE | {'type': 'white'} | __RANGE_255


def _is_int(data):
    try:
        int(data)
        return True
    except:
        return False

def _placeholder(var, value):
    if value.startswith('<') and value.endswith('>'):
        if '-' in value:
            _range = value[1:-1].split('-')
            if len([r for r in _range if not _is_int(r)]) == 0:
                print(f"Explicit_range[{var}]: {_range} overwrite") # TODO: Range check? default overwrite?
                return f"{var}=<range>"
            # Ignore param
            return ""
        # elif ',' in value:                #???
        #    # LIST OPTION OVERWRITE
        #    _list = value[1:-1].split(',')
    # Keep param value
    return f"{var}={value}"


def _generate(type_dict, help_msg):
    func = help_msg.split()[1]
    params = help_msg.split()[2:] if len(help_msg.split()) > 2 else []
    valid_params = []
    for p in params:
        if '=' in p:
            var, value = p.split("=")
            p = _placeholder(var, value)
        else:
            # Empty param fallback
            p = f'{p}=<range>'
        valid_params.append(p)
    type_dict['lm_call'] = f"{func} " + " ".join(valid_params)
    return str(type_dict)

def resolve(help_data, details=False):
    help_msg = []
    for i, msg in enumerate(help_data):
        tag = msg.split()[0].strip()
        # TYPE DECORATION detect in help strings
        if tag[0].isupper():
            resolved_tag = _resolve_key(tag)
            if resolved_tag == tag:
                # TAG NOT FOUND - keep value
                help_msg.append(msg)
                #continue
            if details:
                # Create json string type + help msg details
                help_msg.append(_generate(resolved_tag, msg))
            else:
                # Remove tag - Human readable mode (decorated functions)
                help_msg.append(msg.replace(tag, '').strip())
        elif not details:
            # Human readable mode (non decorated functions)
            help_msg.append(msg)
    return tuple(help_msg)

def _resolve_key(key):
    try:
        type_info = eval(f'{key}')
    except NameError:
        return key
    return type_info
