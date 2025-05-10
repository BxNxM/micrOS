from aioespnow import AIOESPNow
from binascii import hexlify
from Tasks import NativeTask, TaskBase, lm_exec, lm_is_loaded
import uasyncio as asyncio
from Network import get_mac
from Config import cfgget
from Debug import errlog_add


# ----------- PARSE AND RENDER MSG PROTOCOL  --------------

def render_response(tid, oper, data, prompt) -> str:
    """
    Render ESPNow custom message (protocol)
    """
    if oper not in ("REQ", "RSP"):
        errlog_add(f"[ERR] espnow render_response, unknown oper: {oper}")
    tmp = "{tid}|{oper}|{data}|{prompt}$"
    tmp = tmp.replace("{tid}", str(tid))
    tmp = tmp.replace("{oper}", str(oper))
    tmp = tmp.replace("{data}", str(data))
    tmp = tmp.replace("{prompt}", str(prompt))
    return tmp

def parse_request(msg:bytes) -> (bool, dict|str):
    """
    Parse ESPNow custom message protocol
    """
    try:
        msg = msg.decode('utf-8').strip()
    except UnicodeError:
        return False, "Invalid encoding"
    # strip the trailing '$' then split on '|'
    parts = msg.rstrip("$").split("|")
    if len(parts) == 4:
        return True, {"tid": parts[0],
                      "oper": parts[1],
                      "data": parts[2],
                      "prompt": parts[3]}
    return False, f"Missing 4 args: {msg}"


# ----------- ESPNOW SESSION SERVER - LISTENER AND SENDER  --------------
class ResponseRouter:
    """
    Response Router (by mac address)
    to connect sender task with receiver loop (aka server)
    """
    _routes: dict[bytes, "ResponseRouter"] = {}

    def __init__(self, mac: bytes):
        self.mac = mac
        self.response = None
        self._event = asyncio.Event()
        ResponseRouter._routes[mac] = self

    async def get_response(self, timeout:int=10) -> str|dict:
        """Wait for one response, then clear the event for reuse."""
        try:
            await asyncio.wait_for(self._event.wait(), timeout)
        except asyncio.TimeoutError:
            return "Timeout has beed exceeded"
        self._event.clear()
        return self.response

    @staticmethod
    def update_response(mac: bytes, response: str) -> None:
        # USE <tid> for proper session response mapping
        router = ResponseRouter._routes.get(mac)
        if router is None:
            errlog_add(f"[WARN][ESPNOW] No response route for {mac}")
            return
        router.response = response
        router._event.set()

    def close(self) -> None:
        """Remove routing entry when done."""
        ResponseRouter._routes.pop(self.mac, None)


class ESPNowSS:
    """
    ESPNow Session Server
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # first time: actually create it
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # __init__ still runs each time, so guard if needed
        if not hasattr(self, '_initialized'):
            self.espnow = AIOESPNow()                   # Instance with async support
            self.espnow.active(True)
            self.devfid = cfgget('devfid')
            self.devices: dict[bytes, str] = {}         # mapping for { "mac address": "devfid" } pairs
            self._initialized = True
            self.server_ready = False

    # ----------- SERVER METHODS --------------
    def _request_handler(self, msg:bytes, my_task:NativeTask, mac:bytes):
        """
        Handle server input message (request), with REQ/RSP types (oper)
            oper==REQ   - command execution
            oper==RSP   - command response
        :param msg: valid message format> "{tid}|{oper}|{data}|{prompt}$", {data} is the user input
        :param my_task: Server task instance, for my_task.out update
        :param mac: sender binary mac address
        """

        state, request = parse_request(msg)
        if not state:
            my_task.out = f"[_ESPNOW] {request}"
            return state, request

        # parsed request: {"tid": "n/a", "oper": "n/a", "data": "n/a", "prompt": "n/a"}
        operation, prompt, tid = request["oper"], request["prompt"], request["tid"]
        my_task.out = f"[{tid}] {operation} from {prompt}"
        # Update known devices
        self.devices[mac] = request["prompt"]

        # Check if the module/command is allowed., check oper==REQ/RSP
        if operation == "REQ":
            command = request["data"].split()
            module = command[0]
            if lm_is_loaded(module):
                try:
                    state, out = lm_exec(command)
                    # rendered_output: "{tid}|{oper}|{data}|{prompt}$"
                    rendered_out = render_response(tid="?", oper="RSP", data=out, prompt=self.devfid)
                    return state, rendered_out
                except Exception as e:
                    # Optionally log the exception here.
                    state, out = False, f"[ERR][_ESPNOW] {command}: {e}"
            else:
                state, out = False, f"[WARN][_ESPNOW] NotAllowed {module}"
            return state, out
        if operation == "RSP":
            resp_data = request["data"]
            ResponseRouter.update_response(mac, resp_data)          # USE <tid> for proper session response mapping
        return False, f"[_ESPNOW] No action, {request}"

    async def _server(self, tag:str):
        """
        ESPnow async listener task
        :param tag: micro_task tag for task access
        """
        with TaskBase.TASKS.get(tag, None) as my_task:
            self.server_ready = True
            my_task.out = "ESPNow receiver running"
            async for mac, msg in self.espnow:
                try:
                    state, response = self._request_handler(msg, my_task, mac)
                    if state:
                        await self.__asend_raw(mac, response)
                    else:
                        errlog_add(response)
                except OSError as err:
                    # If the peer is not yet added, add it and retry.
                    if len(err.args) > 1 and err.args[1] == 'ESP_ERR_ESPNOW_NOT_FOUND':
                        self.add_peer(mac)
                        state, response = self._request_handler(msg, my_task, mac)
                        if state:
                            await self.__asend_raw(mac, response)
                        else:
                            errlog_add(response)
                    else:
                        # Optionally handle or log other OSErrors here.
                        errlog_add(f"[ERR][NOW SERVER] {err}")

    def start_server(self):
        """
        Start the async ESPNow receiver server.
        """
        # Create an asynchronous task with tag 'espnow.server'
        tag = 'espnow.server'
        state = NativeTask().create(callback=self._server(tag), tag=tag)
        return "Starting" if state else "Already running"

    #----------- SEND METHODS --------------
    async def __asend_raw(self, mac:bytes, msg:str):
        """
        ESPnow send message to mac address
        """
        return await self.espnow.asend(mac, msg.encode("utf-8"))

    async def _asend_task(self, peer:bytes, tag:str, msg:str):
        """
        ESPNow client task: send a command to a peer and update task status.
        """
        with TaskBase.TASKS.get(tag, None) as my_task:
            router = ResponseRouter(peer)
            # rendered_output: "{tid}|{oper}|{data}|{prompt}$"
            rendered_out = render_response(tid="?", oper="REQ", data=msg, prompt=self.devfid)
            if await self.__asend_raw(peer, rendered_out):
                my_task.out = f"[ESPNOW SEND] {rendered_out}"
                my_task.out = await router.get_response()
            else:
                my_task.out = "[ESPNOW SEND] Peer not responding"
            router.close()

    def mac_by_peer_name(self, peer_name:str) -> bytes|None:
        matches = [k for k, v in self.devices.items() if v == peer_name]
        peer = matches[0] if matches else None
        return peer

    def send(self, peer:bytes|str, msg:str) -> str:
        """
        Send a command over ESPNow.
        :param peer: Binary MAC address of another device.
        :param msg: String command message to send.
        """
        peer_name = None
        if isinstance(peer, str):
            # Peer as device name (prompt)
            _peer = self.mac_by_peer_name(peer)
            if _peer is None:
                return f"Unknown device: {peer}"
            peer_name = peer
            peer = _peer

        peer_name = hexlify(peer, ':').decode() if peer_name is None else peer_name
        task_id = f"con.espnow.{peer_name}"
        # Create an asynchronous sending task.
        state = NativeTask().create(callback=INSTANCE._asend_task(peer, task_id, msg), tag=task_id)
        return "Starting" if state else "Already running"

    # ----------- OTHER METHODS --------------

    def add_peer(self, peer:bytes, devfid:str=None):
        """
        Add a peer given its MAC address.
        :param peer: Binary MAC address of a peer (e.g. b'\xbb\xbb\xbb\xbb\xbb\xbb').
        :param devfid: optional parameter to register dev uid for mac address
        """
        try:
            self.espnow.add_peer(peer)
            if devfid is not None:
                # Update known devices
                self.devices[peer] = devfid
        except Exception as e:
            return f"Peer error: {e}"
        return "Peer register done"

    def stats(self):
        """
        Return stats for ESPNow peers.
        stats: tx_pkts, tx_responses, tx_failures, rx_packets, rx_dropped_packets.
        peers: peer, rssi, time_ms.
        """
        try:
            _stats = self.espnow.stats()
        except Exception as e:
            _stats = str(e)
        try:
            _peers = self.espnow.peers_table
        except Exception as e:
            _peers = str(e)
        return {"stats": _stats, "peers": _peers, "map": self.devices, "ready": self.server_ready}


###################################################
#                   Control functions             #
###################################################
INSTANCE = ESPNowSS()

def initialize():
    # TODO: remove, use ESPNowSS() class instead
    global INSTANCE
    if INSTANCE is None:
        INSTANCE = ESPNowSS()
    return INSTANCE


def mac_address():
    """
    Get the binary MAC address.
    """
    return get_mac()