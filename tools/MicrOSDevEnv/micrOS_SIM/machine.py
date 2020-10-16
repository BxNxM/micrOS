
def machine(*args, **kwargs):
    print('machine dummy')
    return 'machine dummy'


def alloc_emergency_exception_buf(*args, **kwargs):
    print('alloc_emergency_exception_buf dummy')
    return 'alloc_emergency_exception_buf dummy'


class Timer:

    def __init__(self, *args, **kwargs):
        pass

    def init(self, *args, **kwargs):
        pass


class Pin:

    def __init__(self, *args, **kwargs):
        pass

    def irq(self, *args, **kwargs):
        pass


class RTC:

    def __init__(self, *args, **kwargs):
        pass

    def datetime(self, *args, **kwargs):
        pass


