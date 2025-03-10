

class AIOESPNow:

    def __init__(self):
        self._active = False
        self.peers_table = None

    def active(self, state=None):
        if state is not None:
            self._active = state
        return self._active

    def stats(self):
        pass

    def add_peer(self, mac):
        pass

    async def asend(self, mac, full_msg):
        pass

    def send(self, mac, full_msg):
        pass

    def __iter__(self):
        return (i for i in range(0, 3))

