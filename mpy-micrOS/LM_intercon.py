from InterConnect import send_cmd


def sendcmd(*args, **kwargs):
    host = kwargs.get('host')
    port = kwargs.get('port', 9008)
    cmd = ' '.join([k.replace(',', '') for k in args])
    return send_cmd(host, port, cmd)


def help():
    return 'sendcmd(cmd, host=<IP>, port=9008)'
