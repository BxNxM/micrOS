from sys import modules
import urequests
from Notify import Notify
from Common import micro_task, syslog, console_write, data_dir, conf_dir
from LM_system import ifconfig
from utime import localtime


def _timestamp():
    _time = [str(k) for k in localtime()[3:6]]
    return ':'.join(_time)


class Telegram(Notify):
    INSTANCE = None
    # Telegram bot token and chat ID
    # https://core.telegram.org/bots/api
    _TOKEN = None  # Telegram token
    _CHAT_IDS = set()  # Telegram bot chat IDs - multi group support - persistent caching
    _API_PARAMS = "?offset=-1&limit=1&timeout=2"  # Generic API params - optimization
    _IN_MSG_ID = None
    _FILE_CACHE = data_dir('telegram.cache')

    def __init__(self, token:str):
        """
        :param token: bot token
        """
        # Subscribe to the notification system - provide send_msg method (over self)
        super().add_subscriber(self)
        Telegram._TOKEN = token
        Telegram.INSTANCE = self

    @staticmethod
    def __id_cache(mode:str):
        """
        File cache
        modes:
            r - recover, s - save
        """
        if mode == 's':
            # SAVE CACHE
            console_write("[NTFY] Save chatIDs cache...")
            with open(Telegram._FILE_CACHE, 'w') as f:
                f.write(','.join([str(k) for k in Telegram._CHAT_IDS]))
            return
        try:
            # RESTORE CACHE
            console_write("[NTFY] Restore chatIDs cache...")
            with open(Telegram._FILE_CACHE, 'r') as f:
                # set() comprehension
                Telegram._CHAT_IDS = {int(k) for k in f.read().strip().split(',')}
        except:
            pass

    @staticmethod
    def __bot_token():
        """Get bot token"""
        if Telegram._TOKEN is None:
            return None
        return Telegram._TOKEN

    @staticmethod
    def send_msg(text:str, *args, **kwargs):
        """
        Send a message to the Telegram chat by chat_id
        :param text: text to send
        :param reply_to: reply to specific message, if None, simple reply
        :param chat_id: chat_id to reply on, if None, reply to all known
        RETURN None when telegram bot token is missing
        """
        reply_to = kwargs.get("reply_to", args[0] if len(args) > 0 else None)
        chat_id = kwargs.get("chat_id", args[1] if len(args) > 1 else None)

        def _send(chid):
            """Send message to chat_id (chid)"""
            data = {"chat_id": chid, "text": f"{Telegram._DEVFID}⚙️\n{text}"}
            if isinstance(reply_to, int):
                data['reply_to_message_id'] = reply_to
                Telegram._IN_MSG_ID = reply_to
            _, _resp = urequests.post(url, headers={"Content-Type": "application/json"}, json=data, jsonify=True,
                                      sock_size=128)
            console_write(f"\tSend message:\n{data}\nresponse:\n{_resp}")
            return _resp

        def _get_chat_ids():
            """Return chat ID or None (in case of no token or cannot get ID)"""
            if len(Telegram._CHAT_IDS) == 0:
                Telegram.get_msg()  # It will update the Telegram.CHAT_IDS
            console_write(f"\tGet chatIDs: {Telegram._CHAT_IDS}")
            return Telegram._CHAT_IDS

        # --------------------- FUNCTION MAIN ------------------------ #
        console_write("[NTFY] SEND MESSAGE")
        # Check bot token
        bot_token = Telegram.__bot_token()
        if bot_token is None:
            return None
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage{Telegram._API_PARAMS}"

        verdict = ""
        # Reply to ALL (notification) - chat_id was not provided
        if chat_id is None:
            console_write("\tREPLY ALL")
            for _chat_id in _get_chat_ids():
                resp_json = _send(chid=_chat_id)
                verdict += f'Sent{_chat_id};' if resp_json['ok'] else str(resp_json)
        else:
            console_write(f"\tREPLY TO {chat_id}")
            # Direct reply to chat_id
            resp_json = _send(chid=chat_id)
            verdict = f'Sent{chat_id}' if resp_json['ok'] else str(resp_json)
        return verdict

    @staticmethod
    def __update_chat_ids(resp_json:dict):
        """
        Update known chat_id-s and cache them
        - return active chat_id frm resp_json
        """
        _cid = None
        if resp_json.get("ok", None) and len(resp_json["result"]) > 0:
            _cid = resp_json["result"][-1]["message"]["chat"]["id"]
            # LIMIT Telegram._CHAT_IDS NOTIFICATION CACHE TO 3 IDs
            if len(Telegram._CHAT_IDS) < 4 and _cid not in Telegram._CHAT_IDS:
                console_write("[NTFY GET] update chatIDs")
                _ids = len(Telegram._CHAT_IDS)
                Telegram._CHAT_IDS.add(_cid)
                if len(Telegram._CHAT_IDS) - _ids > 0:  # optimized save (slow storage access)
                    Telegram.__id_cache('s')
        else:
            Telegram.__id_cache('r')
            if len(Telegram._CHAT_IDS) == 0:
                error_message = resp_json.get("description", "Unknown error")
                raise Exception(f"Error retrieving chat ID: {error_message}")
        return _cid

    @staticmethod
    def get_msg():
        """
        Get the last message from the Telegram chat.
        RETURN None when telegram bot token is missing
        """
        console_write("[NTFY] GET MESSAGE")
        bot_token = Telegram.__bot_token()
        if bot_token is None:
            return None
        response = {'sender': None, 'text': None, 'm_id': -1, 'c_id': None}
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates{Telegram._API_PARAMS}"
        console_write(f"\t[GET] request: {url}")

        _, resp_json = urequests.get(url, jsonify=True, sock_size=128)

        if len(resp_json["result"]) > 0:
            response['c_id'] = Telegram.__update_chat_ids(resp_json)
            resp = resp_json["result"][-1]["message"]
            response['sender'] = f"{resp['chat']['first_name']}{resp['chat']['last_name']}" if resp['chat'].get(
                'username', None) is None else resp['chat']['username']
            response['text'], response['m_id'] = resp['text'], resp['message_id']
        console_write(f"\t\t[GET] response: {response}")
        return response

    @staticmethod
    async def aget_msg():
        """
        Async: Get the last message from the Telegram chat.
        RETURN None when telegram bot token is missing
        """
        console_write("[NTFY] GET MESSAGE")
        bot_token = Telegram.__bot_token()
        if bot_token is None:
            return None
        response = {'sender': None, 'text': None, 'm_id': -1, 'c_id': None}
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates{Telegram._API_PARAMS}"
        console_write(f"\t[aGET] request: {url}")

        _, resp_json = await urequests.aget(url, jsonify=True, sock_size=128)

        if len(resp_json["result"]) > 0:
            response['c_id'] = Telegram.__update_chat_ids(resp_json)
            resp = resp_json["result"][-1]["message"]
            response['sender'] = f"{resp['chat']['first_name']}{resp['chat']['last_name']}" if resp['chat'].get(
                'username', None) is None else resp['chat']['username']
            response['text'], response['m_id'] = resp['text'], resp['message_id']
        console_write(f"\t\t[aGET] response: {response}")
        return response

    @staticmethod
    async def receive_eval():
        """
        READ - VALIDATE - EXECUTE - REPLY LOOP
        - can be used in async loop
        RETURN None when telegram bot token is missing
        """
        console_write("[NTFY] EVAL sequence")
        verdict = None

        def _lm_execute(cmd_args):
            nonlocal verdict, m_id
            status, output = Telegram.lm_execute(cmd_args)
            access = "NotAllowed" not in str(output)
            status = "OK" if status else "NOK"
            if access:
                verdict = f'{_timestamp()} [UP][{status}] Exec: {" ".join(cmd_args[0])}'
                Telegram.send_msg(output, reply_to=m_id)
            else:
                verdict = f'{_timestamp()} [UP][{status}] NoAccess: {cmd_args[0]}'
                Telegram._IN_MSG_ID = m_id

        # -------------------------- FUNCTION MAIN -------------------------- #
        # Async Poll telegram chat
        data = await Telegram.aget_msg()
        if data is None:
            return data
        # Get msg, msg_id, chat_id as main input data source
        msg_in, m_id, c_id = data['text'], data['m_id'], data['c_id']
        if msg_in is not None and m_id != Telegram._IN_MSG_ID:
            # replace single/double quotation to apostrophe (str syntax for repl interpretation)
            msg_in = msg_in.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"')
            if msg_in.startswith('/ping'):
                # Parse loaded modules
                _loaded_mods = [lm.replace('LM_', '') for lm in modules if lm.startswith('LM_')] + ['task']
                Telegram.send_msg(', '.join(_loaded_mods), reply_to=m_id, chat_id=c_id)
            elif msg_in.startswith('/cmd_select'):
                cmd_lm = msg_in.strip().split()[1:]
                # [Compare] cmd selected device param with DEVFID (device/prompt name)
                if cmd_lm[0] in Telegram._DEVFID:
                    _lm_execute(cmd_lm[1:])
                else:
                    verdict = f'{_timestamp()} [UP] NoSelected: {cmd_lm[0]}'
            elif msg_in.startswith('/cmd'):
                cmd_lm = msg_in.strip().split()[1:]
                _lm_execute(cmd_lm)
            elif msg_in.startswith('/notify'):
                param = msg_in.strip().split()[1:]
                if len(param) > 0:
                    verdict = Telegram.notifications(not param[0].strip().lower() in ("disable", "off", 'false'))
                else:
                    verdict = Telegram.notifications()
                # Send is still synchronous (OK)
                Telegram.send_msg(verdict, reply_to=m_id)
        else:
            verdict = f"{_timestamp()} [UP] NoExec"
        return verdict

    @staticmethod
    async def server_bot(tag:str, period:int=3):
        """
        BOT - ReceiveEvalPrintLoop
        :param tag: task tag (access)
        :param period: polling period in sec, default: 3
        """
        cancel_cnt = 0
        period = period if period > 0 else 1
        period_ms = period * 1000
        with micro_task(tag=tag) as my_task:
            my_task.out = f"{_timestamp()} [UP] Running"
            while True:
                # Normal task period
                await my_task.feed(sleep_ms=period_ms)
                try:
                    # await asyncio.wait_for(Telegram.receive_eval(), 5)    # 5 sec timeout???
                    v = await Telegram.receive_eval()
                    my_task.out = "Missing bot token" if v is None else f"{v} ({period}s)"
                    cancel_cnt = 0
                except Exception as e:
                    my_task.out = str(e)
                    # Auto scale - blocking nature - in case of serial failures (5) - hibernate task (increase async sleep)
                    cancel_cnt += 1
                    if cancel_cnt > 5:
                        my_task.out = f"{_timestamp()} [DOWN] {e} (wait 1min)"
                        cancel_cnt = 5
                        # SLOW DOWN - hibernate task
                        await my_task.feed(sleep_ms=60_000)

    @staticmethod
    def set_commands():
        """
        Set Custom Commands to the Telegram chat.
        RETURN None when telegram bot token is missing
        """

        console_write("[NTFY] SET DEFAULT COMMANDS")
        bot_token = Telegram.__bot_token()
        if bot_token is None:
            return None
        url = f"https://api.telegram.org/bot{bot_token}/setMyCommands{Telegram._API_PARAMS}"
        data = {"commands": [{"command": "ping", "description": "Ping All endpoints: list of active modules."},
                             {"command": "notify", "description": "Enable/Disable notifications: on or off"},
                             {"command": "cmd", "description": "Run active module function on all devices."},
                             {"command": "cmd_select",
                              "description": "Same as cmd, only first param must be device name."},
                             ]}
        _, resp_json = urequests.post(url, headers={"Content-Type": "application/json"}, json=data, jsonify=True,
                                      sock_size=128)
        return 'Custom commands was set' if resp_json['ok'] else str(resp_json)

#########################################
#          micrOS Notifications         #
#########################################

def __init(token:str=None):
    token_cache = conf_dir("telegram.token")
    token_refresh = True
    if Telegram.INSTANCE is None:
        # ENABLE TELEGRAM IF NW IS STA - CONNECTED TO THE WEB
        if ifconfig()[0] == "STA":
            if token is None:
                token_refresh = False
                # Attempt to load token from config folder
                try:
                    with open(token_cache, "r") as f:
                        token = f.read()
                except Exception as e:
                    err = f"Telegram: cannot load {token_cache}: {e}"
                    syslog(err)
                    raise Exception(err)
            # Initialize telegram with token
            Telegram(token)
            if token_refresh:
                # Save token
                with open(token_cache, "w") as f:
                    f.write(token)
        else:
            syslog("No STA: cannot init telegram")
    return Telegram.INSTANCE


def load(token:str=None):
    """
    Set custom chat commands for Telegram
    - /ping
    - /cmd module function (params)
    :param token: telegram bot token
    """
    if __init(token) is None:
        return "Network unavailable."
    verdict = Telegram.set_commands()
    return "Missing telegram bot token" if verdict is None else verdict


def send(text:str):
    """
    Send Telegram message - micrOS notification
    :param text: text to send
    return verdict
    """
    if Telegram.INSTANCE is None:
        return "Network unavailable."
    verdict = Telegram.send_msg(text)
    return "Missing telegram bot token" if verdict is None else verdict


def receive():
    """
    Receive Telegram message
    - if all value None, then no incoming messages
    One successful msg receive is necessary to get chat_id for msg send as well!
    """
    if Telegram.INSTANCE is None:
        return "Network unavailable."
    verdict = Telegram.get_msg()
    return "Missing telegram bot token" if verdict is None else verdict


def receiver_loop(period=3):
    """
    Telegram BOT (repl) - ReadEvalPrintLoop for Load Modules
    - Only executes module (function) if the module is already loaded
    :param period: polling period in sec, default: 3
    """
    if Telegram.INSTANCE is None:
        return "Network unavailable or Telegram uninitialized"
    tag = 'telegram.server_bot'
    return micro_task(tag=tag, task=Telegram.server_bot(tag=tag, period=period))


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return ('send "text"',
            'receive',
            'receiver_loop period=3',
            'load token=<your-bot-token>',
            'INFO: Send & Receive messages with Telegram bot')
