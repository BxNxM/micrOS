try:
    from gc import mem_free
except:
    from simgc import mem_free  # simulator mode
from Common import socket_stream


@socket_stream
def raise_error(msgobj=None):
    if msgobj is not None:
        msgobj("Raise test exception")
    raise Exception("Test exception")


@socket_stream
def memory_leak(cnt=160, msgobj=None):
    dict_test = {}
    mem_start = mem_free()
    for k in range(cnt):
        mem = mem_free()
        data = "micrOS memory: Free RAM: {} kB {} byte".format(int(mem / 1024), int(mem % 1024))
        if msgobj is not None:
            msgobj("[{}] gen: {}".format(k, data))
        dict_test[k] = data
    mem_end = mem_free()
    delta = mem_start - mem_end
    return '[{}] RAM Alloc.: {} kB {} byte'.format(len(dict_test), int(delta / 1024), int(delta % 1024))


@socket_stream
def recursion_limit(cnt=14, msgobj=None):
    """
    node01 $  robustness recursion_limit 15
    exec_lm_core LM_robustness->recursion_limit: maximum recursion depth exceeded

    :param cnt: 14
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

