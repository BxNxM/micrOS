import Espnow

def load():
    """
    Initialize ESPNOW protocal
    """
    return Espnow.initialize()

def send(peer:bytes|str, msg:str='modules'):
    """
    Send message to peer (by mac address)
    :param peer: mac address of espnow device
    :param msg: message string/load module call
    """
    now = Espnow.initialize()
    return now.send(peer, msg)

def start_server():
    """
    Start ESPNOW server/listener
    - this can receive espnow messages
    - it includes Load Module execution logic (beta)
    """
    now = Espnow.initialize()
    return now.start_server()

def stats():
    """
    Get ESPNOW stats
    """
    now = Espnow.initialize()
    return now.stats()

def add_peer(peer:bytes, dev_name:str=None):
    """
    Add ESPNOW peer to known hosts
    - It is needed before first send(...)
    """
    now = Espnow.initialize()
    return now.add_peer(peer, dev_name)

def mac_address():
    """
    Get ESPNOW compatible mac address
    """
    return Espnow.mac_address()

def help():
    """
    [beta] ESPNOW sender/receiver with LM execution
    """
    return 'load', 'send <peer> "ping"', 'start_server', 'add_peer <peer> dev_name=None', 'stats', 'mac_address'