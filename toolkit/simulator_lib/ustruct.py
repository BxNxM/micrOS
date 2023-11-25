import struct

def pack(type, data):
    return struct.pack(type, data)


def unpack(type, data):
    return struct.unpack(type, data)

