import Espnow

def load():
    return Espnow.initialize()

def send(peer, msg='ping'):
    return Espnow.espnow_send(peer, msg)

def start_server():
    return Espnow.espnow_server()

def stats():
    return Espnow.stats()

def add_peer(peer):
    now = Espnow.initialize()
    return Espnow.add_peer(now, peer)

def mac_address():
    return Espnow.mac_address()

def help():
    return 'load', 'send <peer> "ping"', 'start_server', 'add_peer <peer>', 'stats', 'mac_address'