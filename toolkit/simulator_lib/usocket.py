import socket as py_socket

_ADDR_HOST_MAP = {}

class _Socket:
    def __init__(self):
        self._sock = py_socket.socket()
        self._micropython_server_hostname = None

    def connect(self, addr):
        self._micropython_server_hostname = _ADDR_HOST_MAP.get(addr)
        return self._sock.connect(addr)

    def __getattr__(self, name):
        return getattr(self._sock, name)

def socket():
    return _Socket()


def getaddrinfo(host, port):
    addrinfo = py_socket.getaddrinfo(host, port)
    ipv4_addrinfo = [ addr for addr in addrinfo if len(addr[-1]) == 2 ]
    for addr in ipv4_addrinfo:
        _ADDR_HOST_MAP[addr[-1]] = host
    if len(addrinfo) != len(ipv4_addrinfo):
        print("[sim] getaddrinfo ipv6 unsupported...")
    return ipv4_addrinfo
