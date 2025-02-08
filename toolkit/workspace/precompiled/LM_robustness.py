from LM_system import memory_usage
from Common import socket_stream, syslog


@socket_stream
def raise_error(msgobj=None):
    """
    Test function - raise  LM exception
    """
    if msgobj is not None:
        msgobj("Raise test exception")
    state = syslog('Robustness TeSt ErRoR')
    raise Exception(f"Test exception: {'OK' if state else 'NOK'}")


@socket_stream
def memory_leak(cnt=160, msgobj=None):
    """
    Test function - allocate lot of memory
    :param cnt: data counter, default 160 iteration
    :return: verdict
    """
    dict_test = {}
    mem_start = memory_usage()['mem_used']
    for k in range(cnt):
        mem = memory_usage()['percent']
        data = "micrOS memory usage: {} %".format(mem)
        if msgobj is not None:
            msgobj("[{}] gen: {}".format(k, data))
        dict_test[k] = data
    mem_end = memory_usage()['mem_used']
    delta = mem_start - mem_end
    return '[{}] RAM Alloc.: {} kB {} byte'.format(len(dict_test), int(delta / 1024), int(delta % 1024))

@socket_stream
def recursion_limit(limit=14, msgobj=None):
    cnt = 0
    for cnt in range(1, limit+1):
        try:
            _recursion(cnt, msgobj=msgobj)
        except Exception as e:
            msgobj(f"ok error: {e}")
            break
    return f"Recursion limit: {cnt}"


def _recursion(cnt, msgobj=None):
    """
    Test function - recursion test
    :param cnt: recursion depth
    :return: verdict
    Error example:
        node01 $  robustness recursion_limit 15
        lm_exec LM_robustness->recursion_limit: maximum recursion depth exceeded
    """
    if cnt > 0:
        remain = _recursion(cnt-1)
        if msgobj is not None:
            msgobj("recalled {}".format(cnt))
    else:
        remain = 0
    return remain


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'NOTE: This is a test module to validate system robustness', \
           'raise_error', 'memory_leak cnt=160', 'recursion_limit cnt=14'

