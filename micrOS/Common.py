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
    """
    Provide socket message object as msgobj
    (SocketServer singleton class)
    """
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs, msgobj=SocketServer().reply_message)
    return wrapper


def transition(from_val, to_val, step_ms, interval_sec):
    """
    Generator for color transitions:
    :param from_val: from value - start from
    :param to_val: to value - target value
    :param step_ms: step to reach to_val - timirq_seq
    :param interval_sec: full interval
    """
    from_val = from_val
    step_cnt = round((interval_sec*1000)/step_ms)
    delta = abs((from_val-to_val)/step_cnt)
    direc = -1 if from_val > to_val else 1

    for cnt in range(0, step_cnt+1):
        yield round(from_val + (cnt * delta) * direc)
