import Espnow


def send(peer:bytes|str, cmd:str='modules'):
    """
    Send message to peer (by mac address)
    :param peer: mac address of espnow device
    :param cmd: message string/load module call
    """
    now = Espnow.initialize()
    return now.send(peer, cmd)

def stats():
    """
    Get ESPNOW stats
    """
    now = Espnow.initialize()
    return now.stats()


def handshake(peer:bytes|str):
    """
    Handshake with ESPNow Peer
    :param peer: mac address of espnow device
    - device name detection
    - address:name caching
    """
    now = Espnow.initialize()
    return now.handshake(peer)


def help():
    """
    ESPNOW sender/receiver with LM execution
    """
    return ('handshake peer=<mac-address>',
            'send peer=<peer-name> cmd="hello"',
            'stats')