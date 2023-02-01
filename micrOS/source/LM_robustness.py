from LM_system import memory_usage
from Common import socket_stream


@socket_stream
def raise_error(msgobj=None):
    """
    Test function - raise  LM exception
    """
    if msgobj is not None:
        msgobj("Raise test exception")
    raise Exception("Test exception")


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
def recursion_limit(cnt=14, msgobj=None):
    """
    Test function - recursion test
    :param cnt: recursion depth
    :return: verdict
    Error example:
        node01 $  robustness recursion_limit 15
        exec_lm_core LM_robustness->recursion_limit: maximum recursion depth exceeded
    """
    if cnt > 0:
        remain = recursion_limit(cnt-1)
        if msgobj is not None:
            msgobj("recalled {}".format(cnt))
    else:
        remain = 0
    return remain


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'NOTE: This is a test module to validate system robustness', \
           'raise_error', 'memory_leak cnt=160', 'recursion_limit cnt=14'

