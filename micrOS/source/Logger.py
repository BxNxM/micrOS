"""
Module is responsible for System and User logging
- built-in log rotation

Designed by Marcell Ban aka BxNxM
"""
from time import localtime
from re import match
from uos import listdir, remove, stat, mkdir, getcwd

#############################################
#        LOGGING WITH DATA ROTATION         #
#############################################
LOG_FOLDER = None

def _init_logger():
    """ Init /logs folder """
    global LOG_FOLDER
    if LOG_FOLDER is None:
        LOG_FOLDER = f"{getcwd()}logs"
        do_create = True
        try:
            if stat(LOG_FOLDER)[0] & 0x4000:
                # Dir exists - skip create
                do_create = False
        except:
            pass
        if do_create:
            try:
                mkdir(LOG_FOLDER)
                syslog(f"[BOOT] log dir {LOG_FOLDER} init")
            except Exception as e:
                LOG_FOLDER = getcwd()
                syslog(f"[BOOT] log dir {LOG_FOLDER} fallback: {e}")
    return LOG_FOLDER


def logger(data, f_name, limit):
    """
    Create generic logger function
    - implements log line rotation
    - automatic time stump
    :param data: input string data to log
    :param f_name: file name to use
    :param limit: line limit for log rotation
    return write verdict - true / false
    INFO: hardcoded max data number = 30
    """
    def _logger(f_mode='r+'):
        nonlocal data, f_name, limit
        limit = min(limit, 30)  # Hardcoded max data line = 30
        # [1] GET TIME STUMP
        ts_buff = [str(k) for k in localtime()]
        ts = ".".join(ts_buff[0:3]) + "-" + ":".join(ts_buff[3:6])
        # [2] OPEN FILE - WRITE DATA WITH TS
        with open(f_name, f_mode) as f:
            _data = f"{ts} {data}\n"
            # read file lines and filter by time stump chunks (hack for replace truncate)
            lines = [_l for _l in f.readlines() if '-' in _l and '.' in _l]
            # get file params
            lines_len = len(lines)
            lines.append(_data)
            f.seek(0)
            # line data rotate
            if lines_len >= limit:
                lines = lines[-limit:]
            # write file
            f.write(''.join(lines))

    f_name = f"{LOG_FOLDER}/{f_name}"
    # Run logger
    try:
        # There is file - append 'r+'
        _logger()
    except:
        try:
            # There is no file - create 'a+'
            _logger('a+')
        except:
            return False
    return True


def log_get(f_name, msgobj=None):
    """
    Get and stream (ver osocket/stdout) .log file's content and count "critical" errors
    - critical error tag in log line: [ERR]
    """
    f_name = f"{LOG_FOLDER}/{f_name}"
    err_cnt = 0
    try:
        if msgobj is not None:
            msgobj(f_name)
        with open(f_name, 'r') as f:
            eline = f.readline().strip()
            while eline:
                # GET error from log line (tag: [ERR])
                err_cnt += 1 if "[ERR]" in eline else 0
                # GIVE BACK .log file contents
                if msgobj is not None:
                    msgobj(f"\t{eline}")
                eline = f.readline().strip()
    except:
        pass
    return err_cnt


def syslog(data=None, msgobj=None):
    if data is None:
        err_cnt = sum([log_get(f, msgobj) for f in listdir(LOG_FOLDER) if f.endswith(".sys.log")])
        return err_cnt

    _match = match(r"^\[([^\[\]]+)\]", data)
    log_lvl = _match.group(1).lower() if _match else 'user'
    f_name = f"{log_lvl}.sys.log" if log_lvl in ("err", "warn", "boot") else 'user.sys.log'
    return logger(data, f_name, limit=4)


def log_clean(msgobj=None):
    to_del = [file for file in listdir(LOG_FOLDER) if file.endswith('.log')]
    for _del in to_del:
        _del = f"{LOG_FOLDER}/{_del}"
        if msgobj is not None:
            msgobj(f" Delete: {_del}")
        remove(_del)

# Init log folder at module load
_init_logger()
