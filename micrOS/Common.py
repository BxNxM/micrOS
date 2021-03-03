"""
Module is responsible for collect the additional
feature definition dedicated to micrOS framework towards LoadModules

socket_stream decorator
- adds an extra msgobj to the wrapped function arg list
- msgobj provides socket msg interface for the open connection

Designed by Marcell Ban aka BxNxM
"""

from SocketServer import SocketServer


def socket_stream(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs, msgobj=SocketServer().reply_message)
    return wrapper
