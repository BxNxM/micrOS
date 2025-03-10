import Espnow

def load():
    """
    Initialize ESPNOW protocal
    """
    return Espnow.initialize()

def send(peer, msg='modules'):
    """
    Send message to peer (by mac address)
    :param peer: mac address of espnow device
    :param msg: message string/load module call
    """
    return Espnow.espnow_send(peer, msg)

def start_server():
    """
    Start ESPNOW server/listener
    - this can receive espnow messages
    - it includes Load Module execution logic (beta)
    """
    return Espnow.espnow_server()

def stats():
    """
    Get ESPNOW stats
    """
    return Espnow.stats()

def add_peer(peer):
    """
    Add ESPNOW peer to known hosts
    - It is needed before first send(...)
    """
    now = Espnow.initialize()
    return Espnow.add_peer(now, peer)

def mac_address():
    """
    Get ESPNOW compatible mac address
    """
    return Espnow.mac_address()

def help():
    """
    [beta] ESPNOW sender/receiver with LM execution
    """
    return 'load', 'send <peer> "ping"', 'start_server', 'add_peer <peer>', 'stats', 'mac_address'