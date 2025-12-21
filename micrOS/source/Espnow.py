"""
ESPNow Session Server and Protocol Utilities

This module implements:
- Custom ESPNow message protocol with transaction IDs (tid) for secure, session-aware communication.
- Asynchronous server and client logic for sending and receiving ESPNow messages.
- Response routing using both MAC address and transaction ID to ensure correct delivery to tasks.
- Peer management, handshake routines, and statistics reporting for ESPNow devices.

Designed for MicroPython environments with async support.
"""


from binascii import hexlify
from json import load, dump
import uasyncio as asyncio
from urandom import getrandbits

from aioespnow import AIOESPNow

from Tasks import NativeTask, lm_exec, lm_is_loaded
from Config import cfgget
from Debug import syslog
from Files import OSPath, path_join, is_file


# ----------- PARSE AND RENDER MSG PROTOCOL  --------------

def render_packet(tid: str, oper: str, data: str, prompt: str) -> str:
    """
    Render ESPNow custom message (protocol)
    """
    if oper not in ("REQ", "RSP"):
        syslog(f"[ERR] espnow render_response, unknown oper: {oper}")
    return f"{tid}|{oper}|{str(data)}|{prompt}$"


def parse_packet(msg: bytes) -> tuple[bool, dict | str]:
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


def get_command_module(request):
    if isinstance(request, dict):
        command = request["data"].split()
        module = command[0]
    elif isinstance(request, str):
        command = request.split()
        module = command[0]
    else:
        command = []
        module = ""
    return command, module


def generate_tid() -> str:
    """
    Generate a secure, random transaction ID (tid).
    Returns an 8-byte hex string.
    """
    return hexlify(bytes([getrandbits(8) for _ in range(8)])).decode()


# ----------- ESPNOW SESSION SERVER - LISTENER AND SENDER  --------------
class ResponseRouter:
    """
    Response Router (by mac address)
    to connect sender task with receiver loop (aka server)
    """
    _routes: dict[tuple[bytes, str], "ResponseRouter"] = {}

    def __init__(self, mac: bytes, tid: str):
        self.mac = mac
        self.tid = tid
        self.response = None
        self._event = asyncio.Event()
        ResponseRouter._routes[(mac, tid)] = self

    async def get_response(self, timeout: int=10) -> str|dict:
        """Wait for one response, then clear the event for reuse."""
        try:
            await asyncio.wait_for(self._event.wait(), timeout)
        except asyncio.TimeoutError:
            return "Timeout has beed exceeded"
        self._event.clear()
        return self.response

    @staticmethod
    def update_response(mac: bytes, tid: str, response: str) -> None:
        router = ResponseRouter._routes.get((mac, tid), None)
        if router is None:
            syslog(f"[WARN][ESPNOW] No response route for {(mac, tid)}")
            return
        router.response = response
        router._event.set()

    def close(self) -> None:
        """Remove routing entry when done."""
        ResponseRouter._routes.pop((self.mac, self.tid), None)


class ESPNowSS:
    """
    ESPNow Session Server
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        # SINGLETON PATTERN
        if cls._instance is None:
            # first time: actually create it
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # __init__ still runs each time, so guard if needed
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.espnow = AIOESPNow()                   # Instance with async support
            self.espnow.active(True)
            self.devfid = cfgget('devfid')
            self.devices: dict[bytes, str] = {}         # mapping for { "mac address": "devfid" } pairs
            self.server_ready = False
            self.peer_cache_path = path_join(OSPath.DATA, "espnow_peers.app_json")
            self._load_peers()

    def _load_peers(self):
        if not is_file(self.peer_cache_path):
            return
        try:
            with open(self.peer_cache_path, 'r', encoding='utf-8') as f:
                devices_map = load(f)
                self.devices = {bytes(k): v for k, v in devices_map}
            for mac in self.devices:
                # PEER REGISTRATION
                self.espnow.add_peer(mac)
        except Exception as e:
            syslog(f"[ERR][ESPNOW] Loading peers: {e}")

    # ----------- SERVER METHODS --------------
    def _request_handler(self, msg: bytes, my_task: NativeTask, mac: bytes):
        """
        Handle server input message (request), with REQ/RSP types (oper)
            oper==REQ   - command execution
            oper==RSP   - command response
        :param msg: valid message format> "{tid}|{oper}|{data}|{prompt}$", {data} is the user input
        :param my_task: Server task instance, for my_task.out update
        :param mac: sender binary mac address
        """

        state, request = parse_packet(msg)
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
            command, module = get_command_module(request)
            # Handle default hello - handshake message
            if len(command) == 1 and module == "hello":
                rendered_out = render_packet(tid=tid, oper="RSP", data=f"hello {prompt}", prompt=self.devfid)
                return True, rendered_out
            # COMMAND EXECUTION
            if lm_is_loaded(module):
                try:
                    state, out = lm_exec(command)
                    # rendered_output: "{tid}|{oper}|{data}|{prompt}$"
                    rendered_out = render_packet(tid=tid, oper="RSP", data=out, prompt=self.devfid)
                    return state, rendered_out
                except Exception as e:
                    # Optionally log the exception here.
                    syslog(f"[ERR][_ESPNOW] {command}: {e}")
                    state, out = False, ""
            else:
                warning_msg = f"[WARN][_ESPNOW] NotAllowed {module}"
                syslog(warning_msg)
                rendered_out = render_packet(tid=tid, oper="RSP", data=warning_msg,
                                               prompt=self.devfid)
                state, out = True, rendered_out
            return state, out
        if operation == "RSP":
            resp_data = request["data"]
            ResponseRouter.update_response(mac, tid, resp_data)          # USE <tid> for proper session response mapping
        #syslog(f"[_ESPNOW] No action, {request}")
        return False, ""

    async def _server(self, tag: str):
        """
        ESPnow async listener task
        :param tag: micro_task tag for task access
        """

        with NativeTask.TASKS.get(tag, None) as my_task:
            self.server_ready = True
            my_task.out = "ESPNow receiver running"
            async for mac, msg in self.espnow:
                reply, response = False, ""
                try:
                    reply, response = self._request_handler(msg, my_task, mac)
                    if reply:
                        await self.__asend_raw(mac, response)
                except OSError as err:
                    # If the peer is not yet added, add it and retry.
                    if len(err.args) > 1 and err.args[1] == 'ESP_ERR_ESPNOW_NOT_FOUND':
                        # AUTOMATIC PEER REGISTRATION
                        self.espnow.add_peer(mac)
                        if reply:
                            await self.__asend_raw(mac, response)
                    else:
                        # Optionally handle or log other OSErrors here.
                        syslog(f"[ERR][NOW SERVER] {err}")

    def start_server(self):
        """
        Start the async ESPNow receiver server.
        """
        # Create an asynchronous task with tag 'espnow.server'
        tag = 'espnow.server'
        return NativeTask().create(callback=self._server(tag), tag=tag)

    #----------- SEND METHODS --------------
    async def __asend_raw(self, mac: bytes, msg: str):
        """
        ESPnow send message to mac address
        """
        return await self.espnow.asend(mac, msg.encode("utf-8"))

    async def _asend_task(self, tid: str, peer: bytes, tag: str, msg: str):
        """
        ESPNow client task: send a command to a peer and update task status.
        """
        with NativeTask.TASKS.get(tag, None) as my_task:
            try:
                router = ResponseRouter(peer, tid)
                # rendered_output: "{tid}|{oper}|{data}|{prompt}$"
                rendered_out = render_packet(tid=tid, oper="REQ", data=msg, prompt=self.devfid)
                if await self.__asend_raw(peer, rendered_out):
                    my_task.out = f"[ESPNOW SEND] {rendered_out}"
                    my_task.out = await router.get_response()
                else:
                    my_task.out = "[ESPNOW SEND] Peer not responding"
            except Exception as e:
                my_task.out = f"[ERR][ESPNOW SEND] {e}"
            finally:
                router.close()

    def mac_by_peer_name(self, peer_name: str) -> bytes | None:
        matches = [k for k, v in self.devices.items() if v == peer_name]
        peer = matches[0] if matches else None
        return peer

    def send(self, peer: bytes | str, msg: str) -> dict:
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
                return {peer: "Unknown device"}
            peer_name = peer
            peer = _peer

        peer_name = hexlify(peer, ':').decode() if peer_name is None else peer_name
        _, module_name = get_command_module(msg)
        task_id = f"con.espnow.{peer_name}.{module_name}"
        tid = generate_tid()
        # Create an asynchronous sending task.
        return NativeTask().create(callback=self._asend_task(tid, peer, task_id, msg), tag=task_id)

    def cluster_send(self, msg):
        """
        Send message for all peers
        """
        _tasks = []
        for peer_name in self.devices.values():
            _tasks.append(self.send(peer_name, msg))
        return _tasks

    # ----------- OTHER METHODS --------------
    def save_peers(self):
        try:
            with open(self.peer_cache_path, "w", encoding="utf-8") as f:
                dump([[list(k), v] for k, v in self.devices.items()], f)
            return True
        except Exception as e:
            syslog(f"[ERR][ESPNOW] Saving peers: {e}")
        return False

    async def _handshake(self, peer: bytes, tag: str):
        """
        Handshake with peer
        - with device caching
        """
        with NativeTask.TASKS.get(tag, None) as my_task:
            if self.devices.get(peer) is None:
                my_task.out = "ESPNow Add Peer"
                try:
                    # PEER REGISTRATION
                    self.espnow.add_peer(peer)
                except Exception as e:
                    my_task.out = f"ESPNow Peer Error: {e}"
                    return
            my_task.out = "Handshake In Progress..."
            sender = self.send(peer, "hello")
            task_key = list(sender.keys())[0]
            sender_task = NativeTask.TASKS.get(task_key, None)
            if sender_task is None:
                my_task.out = "Handshake Error: No sender task"
                return
            result = await sender_task.await_result(timeout=10)
            expected_response =  f"hello {self.devfid}"
            is_ok = False
            if result == expected_response:
                is_ok = self.save_peers()
            my_task.out = f"Handshake: {result} from {self.devices.get(peer)} [{'OK' if is_ok else 'NOK'}]"
            sender_task.cancel()    # Delete sender task (cleanup)

    def _mac_str_to_bytes(self, mac_str: str) -> bytes|None:
        """
        Convert MAC address string (e.g., '50:02:91:86:34:28') to bytes.
        """
        try:
            mac_bytes = bytes(int(x, 16) for x in mac_str.split(":"))
            if len(mac_bytes) != 6:
                return None
            return mac_bytes
        except Exception:
            return None

    def handshake(self, peer: bytes | str):
        """
        Initiate a handshake with a peer device over ESPNow.

        :param peer: The peer device's MAC address as bytes or a string in the format '50:02:91:86:34:28'.
        :return: A dictionary with error information or a NativeTask instance for the handshake operation.
        """
        task_id = "con.espnow.handshake"
        # Create an asynchronous sending task.
        if isinstance(peer, str) and ":" in peer:
            peer_bytes = self._mac_str_to_bytes(peer)
            if peer_bytes is not None:
                peer = peer_bytes
        if isinstance(peer, bytes):
            return NativeTask().create(callback=self._handshake(peer, task_id), tag=task_id)
        return {None: "Invalid MAC address format. Use 50:02:91:86:34:28 or b'P\\x02\\x91\\x864('"}

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
        return {"stats": _stats, "peers": _peers, "ready": self.server_ready}

    def members(self):
        """
        Returns the list of devices that are members of the current group.
        """
        return self.devices

    def remove_peer(self, peer: bytes) -> bool:
        """
        Remove peer from ESPNow devices
        :param peer: MAC address as bytes to remove
        """
        if isinstance(peer, bytes):
            if self.devices.pop(peer, None) is not None:
                self.save_peers()
                self.espnow.del_peer(peer)
                return True
        return False
