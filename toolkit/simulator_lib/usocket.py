import socket as py_socket

def socket():
    return py_socket.socket()


def getaddrinfo(host, port):
    addrinfo = py_socket.getaddrinfo(host, port)
    ipv4_addrinfo = [ addr for addr in addrinfo if len(addr[-1]) == 2 ]
    if len(addrinfo) != len(ipv4_addrinfo):
        print("[sim] getaddrinfo ipv6 unsupported...")
    return ipv4_addrinfo