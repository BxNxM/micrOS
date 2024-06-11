from time import localtime

#############################################
#        LOGGING WITH DATA ROTATION         #
#############################################


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
    def _logger(_data, _f_name, _limit, f_mode='r+'):
        _limit = 30 if _limit > 30 else _limit
        # [1] GET TIME STUMP
        ts_buff = [str(k) for k in localtime()]
        ts = ".".join(ts_buff[0:3]) + "-" + ":".join(ts_buff[3:6])
        # [2] OPEN FILE - WRITE DATA WITH TS
        with open(_f_name, f_mode) as f:
            _data = f"{ts} {_data}\n"
            # read file lines and filter by time stump chunks (hack for replace truncate)
            lines = [_l for _l in f.readlines() if '-' in _l and '.' in _l]
            # get file params
            lines_len = len(lines)
            lines.append(_data)
            f.seek(0)
            # line data rotate
            if lines_len >= _limit:
                lines = lines[-_limit:]
                lines_str = ''.join(lines)
            else:
                lines_str = ''.join(lines)
            # write file
            f.write(lines_str)

    # Run logger
    try:
        # There is file - append 'r+'
        _logger(data, f_name, limit)
    except:
        try:
            # There is no file - create 'a+'
            _logger(data, f_name, limit, 'a+')
        except:
            return False
    return True


def log_get(f_name, msgobj=None):
    """
    Get and stream (ver osocket/stdout) .log file's content and count "critical" errors
    - critical error tag in log line: [ERR]
    """
    err_cnt = 0
    try:
        with open(f_name, 'r') as f:
            eline = f.readline().strip()
            while eline:
                # GET error from log line (tag: [ERR])
                err_cnt += 1 if "[ERR]" in eline else 0
                # GIVE BACK .log file contents
                if msgobj is not None:
                    msgobj(eline)
                eline = f.readline().strip()
    except:
        pass
    return err_cnt


def syslog(data=None, msgobj=None):
    if data is None:
        return log_get('err.log', msgobj)
    return logger(data, 'err.log', limit=6)
