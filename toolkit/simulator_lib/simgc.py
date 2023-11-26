try:
    import psutil
except Exception as e:
    print(f"[SIM][MEM PROFILER] ERROR: {e}")
    psutil = None

MEM_BASELOAD = None

def _get_memory_usage():
    global  MEM_BASELOAD
    if psutil:
        process = psutil.Process()
        memory_info = process.memory_info()
        # Memory usage in bytes
        memory_usage_bytes = memory_info.rss
        if MEM_BASELOAD is None:
            MEM_BASELOAD = 0
        return memory_usage_bytes - MEM_BASELOAD
    return -1000


MEM_BASELOAD = _get_memory_usage()      # HACK: GET MEM BASELOAD - CLOSEST TO REALITY - GET REAL MICROS MEM USAGE


def _get_free_memory():
    if psutil:
        virtual_memory = psutil.virtual_memory()
        # Free memory in bytes
        free_memory_bytes = virtual_memory.available
        return free_memory_bytes
    return -1000


def mem_free(*args, **kwargs):
    return _get_free_memory()


def mem_alloc(*args, **kwargs):
    return _get_memory_usage()


def collect(*args, **kwargs):
    pass
