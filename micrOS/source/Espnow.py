from aioespnow import AIOESPNow
from binascii import hexlify
from Tasks import NativeTask, TaskBase, lm_exec, lm_is_loaded
from Network import get_mac
from Config import cfgget
from Debug import errlog_add

# Configuration values and globals
_INSTANCE = None
_DEVFID = cfgget('devfid')  # for example, "node01"

async def asend(now, mac, msg):
    """
    Send a message over ESPNow. The sent message will be extended with the server prompt.
    The prompt indicates the end-of-message with a '$' marker.
    """
    prompt = f"{_DEVFID}$"  # '$' symbol is the ACK (end of message)!
    # Append a newline and the server prompt to the message.
    full_msg = f"{msg}\n{prompt}".encode("utf-8")
    return await now.asend(mac, full_msg)

def _serv_execute(msg, my_task):
    """
    Process an incoming command and return a tuple (ready, response).

    The function decodes the message, strips any trailing '$' (which marks the prompt),
    and then interprets the message as a command. The command is split into tokens where
    the first token is considered the module/command. If the module is allowed (lm_is_loaded),
    the command is executed with lm_exec; otherwise, "NotAllowed" is returned.
    """
    try:
        command_line = msg.decode('utf-8').strip()
    except UnicodeError:
        my_task.out = "[NOW SERVE] Invalid encoding"
        return False, "Invalid encoding"

    # Split the command into tokens.
    tokens = command_line.split()
    if not tokens:
        return False, "[NOW SERVE] Empty command"
    # Remove trailing prompt marker if present.
    client_token = "?$"
    if tokens[-1].endswith("$"):
        client_token = tokens[-1]
        tokens = tokens[:-1]
    my_task.out = f"[NOW SERVE] {' '.join(tokens)} (from {client_token})"
    # Check if the module/command is allowed.
    module = tokens[0]
    if lm_is_loaded(module):
        try:
            state, out = lm_exec(tokens)
        except Exception as e:
            # Optionally log the exception here.
            state, out = False, f"[ERR][NOW SERVE] {tokens}: {e}"
    else:
        state, out = False, f"[WARN][NOW SERVE] NotAllowed {tokens[0]}"
    return state, out

async def _server(now):
    """
    ESPNow server task that continuously waits for incoming messages and processes commands.
    """
    with TaskBase.TASKS.get('espnow.server', None) as my_task:
        async for mac, msg in now:
            try:
                state, response = _serv_execute(msg, my_task)
                if state:
                    await asend(now, mac, response)
                else:
                    errlog_add(response)
            except OSError as err:
                # If the peer is not yet added, add it and retry.
                if len(err.args) > 1 and err.args[1] == 'ESP_ERR_ESPNOW_NOT_FOUND':
                    now.add_peer(mac)
                    state, response = _serv_execute(msg, my_task)
                    if state:
                        await asend(now, mac, response)
                    else:
                        errlog_add(response)
                else:
                    # Optionally handle or log other OSErrors here.
                    errlog_add(f"[ERR][NOW SERVER] {err}")

async def _send(now, peer, tag, msg):
    """
    ESPNow client task: send a command to a peer and update task status.
    """
    with TaskBase.TASKS.get(tag, None) as my_task:
        if not await asend(now, peer, msg):
            my_task.out = "[NOW SEND] Peer not responding"
        else:
            my_task.out = f"[NOW SEND] {msg}"

###################################################
#                   Control functions             #
###################################################
def initialize():
    """
    Initialize the ESPNow protocol. (WLAN must be active.)
    """
    global _INSTANCE
    if _INSTANCE is None:
        now = AIOESPNow()  # Instance with async support
        now.active(True)
        _INSTANCE = now
    return _INSTANCE

def add_peer(now, peer):
    """
    Add a peer given its MAC address.
    :param now: ESPNow instance.
    :param peer: Binary MAC address of a peer (e.g. b'\xbb\xbb\xbb\xbb\xbb\xbb').
    """
    now.add_peer(peer)
    return "Peer register done"

def espnow_server():
    """
    Start the async ESPNow receiver server.
    """
    now = initialize()
    # Create an asynchronous task with tag 'espnow.server'
    state = NativeTask().create(callback=_server(now), tag='espnow.server')
    return "Starting" if state else "Already running"

def espnow_send(peer, msg):
    """
    Send a command over ESPNow.
    :param peer: Binary MAC address of another device.
    :param msg: String command message to send.
    """
    now = initialize()
    mac_str = hexlify(peer, ':').decode()
    task_id = f"espnow.cli.{mac_str}"
    # Create an asynchronous sending task.
    state = NativeTask().create(callback=_send(now, peer, task_id, msg), tag=task_id)
    return "Starting" if state else "Already running"

def stats():
    """
    Return stats for ESPNow peers.
    stats: tx_pkts, tx_responses, tx_failures, rx_packets, rx_dropped_packets.
    peers: peer, rssi, time_ms.
    """
    now = initialize()
    try:
        _stats = now.stats()
    except Exception as e:
        _stats = str(e)
    try:
        _peers = now.peers_table
    except Exception as e:
        _peers = str(e)
    return {"stats": _stats, "peers": _peers}

def mac_address():
    """
    Get the binary MAC address.
    """
    return get_mac()