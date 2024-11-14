import uasyncio as asyncio
from aioespnow import AIOESPNow
from binascii import hexlify
from Tasks import NativeTask, TaskBase
from Network import get_mac
from Config import cfgget

# https://docs.micropython.org/en/latest/library/espnow.html
_INSTANCE = None
_DEVFID = cfgget('devfid')


async def asend(now, mac, msg):
    prompt = f"{_DEVFID}$"
    msg = f"{msg}\n{prompt}".encode("utf-8")
    return await now.asend(mac, msg)


def execute(msg, my_task):
    msg_in = msg.decode('utf-8')
    if msg_in.strip().endswith("$"):
        my_task.out = f"MSG-IN: {msg_in}"
        data = msg_in.split("\n")
        prompt, command = data[0], data[1]
        msg_out = f"RUN CMD: {command} ON {prompt.replace('$', '')}"
        # TODO: execute command
        return True, msg_out
    return False, ""


# Echo any received messages back to the sender
async def _server(now):
    with TaskBase.TASKS.get('espnow.server', None) as my_task:
        async for mac, msg in now:
            try:
                msg_ready, msg = execute(msg, my_task)
                if msg_ready:
                    await asend(now, mac, msg)
            except OSError as err:
                if len(err.args) > 1 and err.args[1] == 'ESP_ERR_ESPNOW_NOT_FOUND':
                    now.add_peer(mac)
                    msg_ready, msg = execute(msg, my_task)
                    if msg_ready:
                        await asend(now, mac, msg)


# Send a periodic ping to a peer
async def _send(now, peer, tag, msg):
    with TaskBase.TASKS.get(tag) as my_task:
        if not await asend(now, peer, msg):
            my_task.out = "Peer not responding"
        else:
            my_task.out = f"send msg: {msg}"


###################################################
#                   Control functions             #
###################################################
def initialize():
    """
    Initialize ESPNow protocol
    """
    # Network module: WLAN interface must be active to send()/recv()
    global _INSTANCE
    if _INSTANCE is None:
        now = AIOESPNow()  # Returns AIOESPNow enhanced with async support
        now.active(True)
        _INSTANCE = now
    return _INSTANCE


def add_peer(now, peer):
    """
    Add peer by mac address
    :param now: espnow instance
    :param peer: binary mac address of a peer, like b'\xbb\xbb\xbb\xbb\xbb\xbb'
    """
    return now.add_peer(peer)


def espnow_server():
    """
    Start async ESPNow receiver server
    """
    now = initialize()
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    state = NativeTask().create(callback=_server(now), tag='espnow.server')
    return "Starting" if state else "Already running"


def espnow_send(peer, msg):
    """
    Send message/command over ESPNow protocol
    :param peer: binary mac address of another device
    :param msg: string message to send
    """
    now = initialize()
    mac = hexlify(peer, ':').decode()
    task_id = f"espnow.cli.{mac}"
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    state = NativeTask().create(callback=_send(now, peer, task_id, msg), tag=task_id)
    return "Starting" if state else "Already running"


def stats():
    """
    Return stats for ESPNow peers
    stats: tx_pkts, tx_responses, tx_failures, rx_packets, rx_dropped_packets
    peers: peer, rssi, time_ms
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
    Get binary mac address
    """
    return get_mac()