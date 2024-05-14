"""
micrOS STANDARDIZED Widget / UI interface types v1
- returns type specific input information in dict
- RANGE: int tuple type: (min:int, max:int, step:int)
- MATRIX: bool tuple type: (default:bool/None, state1:bool, state2*:bool)
"""

# OPTION KEY VALUES
# int param range: (min, max, step)
_channel = (0, 255, 1)          # CHANNEL (min, max, step) r|g|b|c|w input param RANGE
_percent = (0, 100, 1)          # PERCENT (min, max, step) input param RANGE
_time_range_s = (0, 21600, 10)  # TRAN_WHITE / TRAN_COLOR input param RANGE
_time_range_ms = (0, 300, 2)    # TRAN_WHITE / TRAN_COLOR input param RANGE
# bool param list, first is the default
_state = (None, True, False)    # STATE input param MATRIX
_smooth = (True, False)         # SMOOTH input param MATRIX
_wake = (True, False)           # WAKE input param MATRIX
# Optional keys (can be ignored as input)
_OPTIONAL = ('smooth', 'wake', 'speed_ms')


########################################################
#                   FUNC-WIDGET TYPES                  #
########################################################

# COLOR type: r|g|b(min, max, step)
COLOR = {'r': _channel, 'g': _channel, 'b': _channel,
         'smooth': _smooth, 'wake': _wake}
# CCT COLOR
WHITE = {'cw': _channel, 'ww': _channel, 'smooth': _smooth, 'wake': _wake}

# BRIGHTNESS type: percent(min, max, step)
BRIGHTNESS = {'percent': _percent,
              'smooth': _smooth, 'wake': _wake}

# TOGGLE type:
TOGGLE = {'state': _state, 'smooth': _smooth}

# TRANSITION
TRAN_WHITE = {'cw': _channel, 'ww': _channel, 'sec': _time_range_s, 'wake': _wake}
TRAN_COLOR = {'r': _channel, 'g': _channel, 'b': _channel, 'sec': _time_range_s, 'wake': _wake}

# BUTTON type
BUTTON = {}

# JOYSTICK type
JOYSTICK = {'x': _percent, 'y': _percent, 'speed_ms': _time_range_ms, 'smooth': _wake}

# INFO type
INFO = BUTTON


# TASK ?

# CUSTOM ?

########################################################
#                 HELP TUPLE RESOLVER                  #
########################################################

def resolve(help_data, details=False):
    help_msg = []
    for i, h in enumerate(help_data):
        tag = h.split()[0]
        resolved_tag = _resolve_key(tag)
        if resolved_tag == tag:
            # TAG NOT FOUND - keep value
            help_msg.append(help_data[i])
            continue
        if details:
            help_msg.append(help_data[i].replace(tag, f":{tag}:{resolved_tag}"))
        else:
            help_msg.append(help_data[i].replace(tag, '').strip())
    if details:
        help_msg.append(f":_OPTIONAL: {_OPTIONAL}")
    return tuple(help_msg)

def _resolve_key(key):
    try:
        type_info = eval(f'{key}')
    except NameError:
        return key
    return type_info
