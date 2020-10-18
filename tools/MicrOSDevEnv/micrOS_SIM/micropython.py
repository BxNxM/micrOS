from sim_console import console
import resource


def alloc_emergency_exception_buf(*args, **kwargs):
    console('alloc_emergency_exception_buf dummy')
    return 'alloc_emergency_exception_buf dummy'


def mem_info(*args, **kwargs):
    usage = resource.getrusage(resource.RUSAGE_SELF)
    max_mem = usage.ru_maxrss / 1024 / 1024        # bytes by default
    console("Max RAM usage: {:.2f} Mb".format(max_mem))
    return max_mem


if __name__ == "__main__":
    mem_info()
