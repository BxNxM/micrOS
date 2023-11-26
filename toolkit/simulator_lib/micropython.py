from sim_console import console
try:
    import resource
except Exception as e:
    console("resource module import error: {}".format(e))
    resource = None


def alloc_emergency_exception_buf(*args, **kwargs):
    console('alloc_emergency_exception_buf dummy')
    return 'alloc_emergency_exception_buf dummy'


def mem_info(*args, **kwargs):
    if resource is None:
        max_mem = "n/a"
    else:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        max_mem = usage.ru_maxrss / 1024 / 1024        # bytes by default
    if isinstance(max_mem, float):
        console("Max RAM usage: {:.2f} Mb".format(max_mem))
    else:
        console("Max RAM usage: {} Mb".format(max_mem))
    total_heap, used_heap, free_heap = -1, max_mem, -1
    return total_heap, used_heap, free_heap


def const(*args):
    return args


def schedule(callback, arg):
    return callback(arg)


def heap_lock():
    pass


def heap_unlock():
    pass


if __name__ == "__main__":
    mem_info()
