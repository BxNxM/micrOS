import micropython

def mem_free(*args, **kwargs):
    try:
        return " {:.2f} Mb".format(micropython.mem_info())
    except Exception as e:
        return "mem_free error: {}".format(e)


def collect(*args, **kwargs):
    pass
