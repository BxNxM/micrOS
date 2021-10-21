import time as pytime


def sleep(sec):
    pytime.sleep(sec)


def sleep_ms(ms):
    pytime.sleep(ms*0.001)


def localtime(sec=None):
    def __convert_localtime(struct_time):
        return (struct_time.tm_year,
                struct_time.tm_mon,
                struct_time.tm_mday,
                struct_time.tm_hour,
                struct_time.tm_min,
                struct_time.tm_sec,
                struct_time.tm_wday,
                struct_time.tm_yday)
    if sec:
        return __convert_localtime(pytime.localtime(sec))
    return __convert_localtime(pytime.localtime())


def sleep_us(us):
    pytime.sleep(us*0.000001)


def time():
    return pytime.time()

