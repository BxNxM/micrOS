import socket as py_socket

def socket():
    return py_socket.socket()


def getaddrinfo(host, port):
    return py_socket.getaddrinfo(host, port)