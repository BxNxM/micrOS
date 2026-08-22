"""
Module is responsible for System and User logging
- built-in log rotation

Designed by Marcell Ban aka BxNxM
"""
from time import localtime
from re import match
from uos import remove
from Files import OSPath, path_join, ilist_fs, is_dir

#############################################
#        LOGGING WITH DATA ROTATION         #
#############################################

def _init_logger():
    """ Init /logs folder """
    if not is_dir(OSPath.LOGS):
        OSPath.LOGS = OSPath._ROOT
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
        limit = 1 if limit <= 0 else min(limit, 30)  # Hardcoded max data line = 30
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
        with open(f_path, 'w') as f:
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


def log_get(f_name:str):
    """
    Generic file getter for .log files
    - return file content
    """
    f_path = path_join(_dir_select(f_name), f_name)
    try:
        with open(f_path, 'r') as f:
            return f.read()
    except:
        return ''


def syslog(data=None, dump=False):
    """
    System log setter/getter
    :param data: None - read logs, str - write logs
    :param dump: include log file path/text entries in read response
    """
    if data is None:
        # READ LOGS
        err_cnt = 0
        logs = {}
        for f_name in (f for f in ilist_fs(OSPath.LOGS, type_filter='f') if f.endswith(".sys.log")):
            text = log_get(f_name)
            err_cnt += sum(1 for line in text.splitlines() if "[ERR]" in line)
            if dump:
                logs[path_join(OSPath.LOGS, f_name)] = text
        health = err_cnt == 0
        output = {'health': health,
                  'verdict': f"{'OK' if health else 'NOK'} alarm: {err_cnt}"}
        if dump:
            output.update(logs)
        return output
    # WRITE LOGS - [target].sys.log automatic log level detection
    _match = match(r"^\[([^\[\]]+)\]", data)
    log_lvl = _match.group(1).lower() if _match else 'user'
    f_name = f"{log_lvl}.sys.log" if log_lvl in ("err", "warn", "boot", "info") else 'user.sys.log'
    return logger(data, f_name, limit=4)


def log_clean():
    """
    Clean logs folder
    """
    logs_dir = OSPath.LOGS
    to_del = [file for file in ilist_fs(logs_dir, type_filter='f') if file.endswith('.log')]
    deleted = []
    for _del in to_del:
        _del = path_join(logs_dir, _del)
        deleted.append(f" Delete: {_del}")
        remove(_del)
    return '\n'.join(deleted)

# Init log folder at module load
_init_logger()
