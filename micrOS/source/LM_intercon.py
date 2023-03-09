from InterConnect import send_cmd, dump_cache
from Debug import errlog_add


def sendcmd(*args, **kwargs):
    """
    Implements send command function towards micrOS devices
        example: sendcmd "hello" host="IP/hostname.local") OR sendcmd host="IP/hostname.local" cmd="system rssi")
    :param host[0]: host IP or Hostname
    :param cmd[1]: command - module func arg(s)
    :return str: reply
    """
    def __send(_host, _cmd):
        try:
            out = send_cmd(_host, _cmd)
        except Exception as e:
            out = []
            errlog_add(f'[intercon] sendcmd: {e}')
        return out

    host = kwargs.get('host', None)
    cmd = kwargs.get('cmd', None)

    # Host correction (exec_lm_core) if keyword-arg 'host' was not found
    if host is None:
        host = args[0]
        args = args[1:]

    # Cmd correction (exec_lm_core) if keyword-arg was not found
    if cmd is None:
        cmd = ''.join(args)
    return __send(host, cmd)


def dump():
    """
    Dump intercon connection cache
    :return dict: device-ip pairs
    """
    return dump_cache()


#######################
# LM helper functions #
#######################

def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'sendcmd "hello" host="IP/hostname.local") OR sendcmd host="IP/hostname.local" cmd="system rssi")', \
           'example: intercon sendcmd "10.0.1.84" "system rssi" OR intercon sendcmd "system rssi" host="node01.local"', \
           'dump (dump host cache)'
