"""
Module is responsible for System and User logging
- built-in log rotation

Designed by Marcell Ban aka BxNxM
"""
from time import localtime
from re import match
from uos import remove, mkdir
from Files import OSPath, path_join, ilist_fs, is_dir

#############################################
#        LOGGING WITH DATA ROTATION         #
#############################################

def _init_logger():
    """ Init /logs folder """
    if not is_dir(OSPath.LOGS):
        try:
            mkdir(OSPath.LOGS)
            syslog(f"[BOOT] log dir {OSPath.LOGS} init")
        except Exception as e:
            OSPath.LOGS = OSPath.ROOT
            syslog(f"[BOOT] log dir {OSPath.LOGS} fallback: {e}")
    return OSPath.LOGS


def _dir_select(f_name:str) -> str:
    """
    Select log dir based on file extension
    :param f_name: filename with extension to detect target dir
    """
    if f_name.endswith(".log"):
        return OSPath.LOGS
    return OSPath.DATA


def logger(data, f_name:str, limit:int):
    """
    Generic logger function with line rotation and time
    :param data: data to log
    :param f_name: file name to use
    :param limit: line limit for log rotation
    return write verdict - true / false
    INFO: hardcoded max data number = 30
    """
    def _logger(f_mode='r+'):
        nonlocal data, f_path, limit
        limit = min(limit, 30)  # Hardcoded max data line = 30
        # [1] GET TIME STUMP
        ts_buff = [str(k) for k in localtime()]
        ts = ".".join(ts_buff[0:3]) + "-" + ":".join(ts_buff[3:6])
        # [2] OPEN FILE - WRITE DATA WITH TS
        with open(f_path, f_mode) as f:
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

    f_path = path_join(_dir_select(f_name), f_name)
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


def log_get(f_name:str, msgobj=None):
    """
    Generic file getter for .log files
    - log content critical [ERR] counter
    """
    f_path = path_join(_dir_select(f_name), f_name)
    err_cnt = 0
    try:
        if msgobj is not None:
            msgobj(f_path)
        with open(f_path, 'r') as f:
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
    """
    System log setter/getter
    :param data: None - read logs, str - write logs
    :param msgobj: function to stream .log files
    """
    if data is None:
        # READ LOGS
        err_cnt = sum([log_get(f, msgobj) for f in ilist_fs(OSPath.LOGS, type_filter='f') if f.endswith(".sys.log")])
        return err_cnt
    # WRITE LOGS - [target].sys.log automatic log level detection
    _match = match(r"^\[([^\[\]]+)\]", data)
    log_lvl = _match.group(1).lower() if _match else 'user'
    f_name = f"{log_lvl}.sys.log" if log_lvl in ("err", "warn", "boot", "info") else 'user.sys.log'
    return logger(data, f_name, limit=4)


def log_clean(msgobj=None):
    """
    Clean logs folder
    """
    logs_dir = OSPath.LOGS
    to_del = [file for file in ilist_fs(logs_dir, type_filter='f') if file.endswith('.log')]
    for _del in to_del:
        _del = path_join(logs_dir, _del)
        if msgobj is not None:
            msgobj(f" Delete: {_del}")
        remove(_del)

# Init log folder at module load
_init_logger()
