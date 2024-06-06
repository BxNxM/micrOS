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
from Debug import errlog_add

########################################################
#                 HELP TUPLE RESOLVER                  #
########################################################
__TEMPLATE = {'type': 'n/a', 'lm_call': ''}
# range and options param types
__RANGE_100 = {'range': (0, 100, 2)}
__RANGE_255 = {'range': (0, 255, 2)}
__RANGE_OPTS = {'options': ("True", "False")}


# WIDGET TYPES - STRUCTURE (DYNAMIC)
BUTTON = __TEMPLATE | {'type': 'button'}                                    # Mandatory func params: n/a
TOGGLE = __TEMPLATE | {'type': 'toggle'} | __RANGE_OPTS                     # Mandatory func params: state
SLIDER = __TEMPLATE | {'type': 'slider'} | __RANGE_100                      # Mandatory func params: br
TEXTBOX = __TEMPLATE | {'type': 'textbox', 'refresh': 10000}                # Mandatory func params: n/a
COLOR = __TEMPLATE | {'type': 'color'} | __RANGE_255                        # Mandatory func params: r, g, b
WHITE = __TEMPLATE | {'type': 'white'} | __RANGE_255                        # Mandatory func params: wc, ww


########################################################
#                       FUNCTIONS                      #
########################################################

def _placeholder(var, value, type_dict):
    def _is_int(data):
        try:
            int(data)
            return True
        except:
            return False

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
                return f"{var}=:range:", new_range, 'range'
            # Ignore param
            return "", None, None
        if ',' in value:
            _opts = value[1:-1].split(',')
            new_opts = tuple(_opts)
            return f"{var}=:options:", new_opts, 'options'
    # Keep param value
    return f"{var}={value}", None, None


def _generate(type_dict, help_msg):
    func = help_msg.split()[1]
    params = help_msg.split()[2:] if len(help_msg.split()) > 2 else []
    valid_params = []
    for p in params:
        if '=' in p:
            var, value = p.split("=")
            try:
                p, values, value_type = _placeholder(var, value, type_dict)
                if value_type is not None:
                    type_dict[value_type] = values
            except Exception as e:
                errlog_add(f"[ERR] Type.resolve._placeholder: {e}")
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
            try:
                resolved_tag = eval(tag)
            except:
                resolved_tag = tag
            if widgets:
                if isinstance(resolved_tag, dict):
                    # Create json string type + extract widgets from help message
                    help_msg.append(_generate(resolved_tag, msg))
                continue
            # Human readable mode (decorated functions)
            help_msg.append(msg.replace(tag, '').strip())
        elif not widgets:
            # Human readable mode (non decorated functions)
            help_msg.append(f"{msg}")
    return tuple(help_msg)
