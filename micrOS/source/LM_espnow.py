import Espnow


def send(peer:bytes|str, msg:str='modules'):
    """
    Send message to peer (by mac address)
    :param peer: mac address of espnow device
    :param msg: message string/load module call
    """
    now = Espnow.initialize()
    return now.send(peer, msg)

def stats():
    """
    Get ESPNOW stats
    """
    now = Espnow.initialize()
    return now.stats()


def add_peer(peer:bytes, dev_name:str=None):
    """
    OBSOLETE
    Legacy function - use handshake instead
    """
    return handshake(peer)


def handshake(peer:bytes):
    """
    Handshake with ESPNow Peer
    :param peer: mac address of espnow device
    - device name detection
    - address:name caching
    """
    now = Espnow.initialize()
    return now.handshake(peer)


def mac_address():
    """
    Get ESPNOW compatible mac address
    """
    return Espnow.mac_address()


def help():
    """
    [beta] ESPNOW sender/receiver with LM execution
    """
    return ('send <peer> "hello"',
            'stats',
            'mac_address',
            'handshake peer <bytes>')