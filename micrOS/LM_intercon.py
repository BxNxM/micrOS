from InterConnect import send_cmd


def sendcmd(*_args, **kwargs):
    host = kwargs.get('host')
    port = kwargs.get('port', 9008)
    args = kwargs.get('args', None)
    if args is None:
        cmd = ' '.join([k.replace(',', '') for k in _args])
        return send_cmd(host, port, cmd)
    cmd = ' '.join([k.replace(',', '') for k in args.strip().split()])
    return send_cmd(host, port, cmd)


#######################
# LM helper functions #
#######################

def help():
    return 'sendcmd <cmd> host=<IP>, port=9008) OR sendcmd host=<IP>, port=9008 args="<cmd>")', \
           'example: intercon sendcmd "dimmer" "toggle" host="10.0.1.84" OR intercon sendcmd host="10.0.1.84" args="dimmer toggle"'
