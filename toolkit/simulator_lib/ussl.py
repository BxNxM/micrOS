class _MicroPythonSSLWrapper:
    def __init__(self, sock):
        self._sock = sock

    def read(self, size=-1):
        reader = getattr(self._sock, "read", None)
        if callable(reader):
            return reader(size)
        return self._sock.recv(size)

    def write(self, data):
        writer = getattr(self._sock, "write", None)
        if callable(writer):
            return writer(data)
        return self._sock.send(data)

    def close(self):
        return self._sock.close()

    def __getattr__(self, name):
        return getattr(self._sock, name)


def _as_micropython_stream(sock):
    if hasattr(sock, "read") and hasattr(sock, "write"):
        return sock
    return _MicroPythonSSLWrapper(sock)


def wrap_socket(sock, server_side=False, key=None, cert=None, cert_reqs=None,
                cadata=None, server_hostname=None, do_handshake=True):
    try:
        from ssl import _create_unverified_context
        context = _create_unverified_context()
        if server_hostname is None:
            server_hostname = getattr(sock, "_micropython_server_hostname", None)
        return _as_micropython_stream(context.wrap_socket(sock, server_side=server_side,
                                                          server_hostname=server_hostname,
                                                          do_handshake_on_connect=do_handshake))
    except Exception as e:
        print(f"[SIMULATOR][WRAP] ERROR - SSL wrap failed: {e}")
    return _as_micropython_stream(sock)
