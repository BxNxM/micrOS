from sys import modules
import urequests
from Notify import Notify
from Config import cfgget
from Common import micro_task, syslog, console_write
from LM_system import ifconfig


class Telegram(Notify):
    # Telegram bot token and chat ID
    # https://core.telegram.org/bots/api
    _TOKEN = None  # Telegram token
    _CHAT_IDS = set()  # Telegram bot chat IDs - multi group support - persistent caching
    _API_PARAMS = "?offset=-1&limit=1&timeout=2"  # Generic API params - optimization
    _IN_MSG_ID = None

    def __init__(self):
        # Subscribe to the notification system - provide send_msg method (over self)
        super().add_subscriber(self)

    @staticmethod
    def __id_cache(mode):
        """
        pds - persistent data structure
        modes:
            r - recover, s - save
        """
        if mode == 's':
            # SAVE CACHE
            console_write("[NTFY] Save chatIDs cache...")
            with open('telegram.pds', 'w') as f:
                f.write(','.join([str(k) for k in Telegram._CHAT_IDS]))
            return
        try:
            # RESTORE CACHE
            console_write("[NTFY] Restore chatIDs cache...")
            with open('telegram.pds', 'r') as f:
                # set() comprehension
                Telegram._CHAT_IDS = {int(k) for k in f.read().strip().split(',')}
        except:
            pass

    @staticmethod
    def __bot_token():
        """Get bot token"""
        if Telegram._TOKEN is None:
            token = cfgget('telegram')
            if token is None or token == 'n/a':
                return None
            Telegram._TOKEN = token
        return Telegram._TOKEN

    @staticmethod
    def send_msg(text, reply_to=None, chat_id=None):
        """
        Send a message to the Telegram chat by chat_id
        :param text: text to send
        :param reply_to: reply to specific message, if None, simple reply
        :param chat_id: chat_id to reply on, if None, reply to all known
        RETURN None when telegram bot token is missing
        """

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
    def __update_chat_ids(resp_json):
        """
        Update known chat_id-s and cache them
        - return active chat_id frm resp_json
        """
        console_write("[NTFY GET] update chatIDs")
        _cid = None
        if resp_json.get("ok", None) and len(resp_json["result"]) > 0:
            _cid = resp_json["result"][-1]["message"]["chat"]["id"]
            # LIMIT Telegram._CHAT_IDS NOTIFICATION CACHE TO 3 IDs
            if len(Telegram._CHAT_IDS) < 4:
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
        console_write(f"\t1/2[GET] request: {url}")

        _, resp_json = urequests.get(url, jsonify=True, sock_size=128)

        if len(resp_json["result"]) > 0:
            response['c_id'] = Telegram.__update_chat_ids(resp_json)
            resp = resp_json["result"][-1]["message"]
            response['sender'] = f"{resp['chat']['first_name']}{resp['chat']['last_name']}" if resp['chat'].get(
                'username', None) is None else resp['chat']['username']
            response['text'], response['m_id'] = resp['text'], resp['message_id']
        console_write(f"\t2/2[GET] response: {response}")
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
        console_write(f"\t1/2[GET] request: {url}")

        _, resp_json = await urequests.aget(url, jsonify=True, sock_size=128)

        if len(resp_json["result"]) > 0:
            response['c_id'] = Telegram.__update_chat_ids(resp_json)
            resp = resp_json["result"][-1]["message"]
            response['sender'] = f"{resp['chat']['first_name']}{resp['chat']['last_name']}" if resp['chat'].get(
                'username', None) is None else resp['chat']['username']
            response['text'], response['m_id'] = resp['text'], resp['message_id']
        console_write(f"\t2/2[GET] response: {response}")
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

        def lm_execute(cmd_args):
            nonlocal verdict, m_id
            access, output = Telegram.lm_execute(cmd_args)
            if access:
                verdict = f'[UP] Exec: {" ".join(cmd_args[0])}'
                Telegram.send_msg(output, reply_to=m_id)
            else:
                verdict = f'[UP] NoAccess: {cmd_args[0]}'
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
                    lm_execute(cmd_lm[1:])
                else:
                    verdict = f'[UP] NoSelected: {cmd_lm[0]}'
            elif msg_in.startswith('/cmd'):
                cmd_lm = msg_in.strip().split()[1:]
                lm_execute(cmd_lm)
            elif msg_in.startswith('/notify'):
                param = msg_in.strip().split()[1:]
                if len(param) > 0:
                    verdict = Telegram.notifications(not param[0].strip().lower() in ("disable", "off", 'false'))
                else:
                    verdict = Telegram.notifications()
                # Send is still synchronous (OK)
                Telegram.send_msg(verdict, reply_to=m_id)
        else:
            verdict = "[UP] NoExec"
        console_write(f"\tBOT: {verdict}")
        return verdict

    @staticmethod
    async def bot_repl(tag, period=3):
        """
        BOT - ReceiveEvalPrintLoop
        :param tag: task tag (access)
        :param period: polling period in sec, default: 3
        """
        cancel_cnt = 0
        period = period if period > 0 else 1
        period_ms = period * 1000
        with micro_task(tag=tag) as my_task:
            my_task.out = "[UP] Running"
            while True:
                # Normal task period
                await my_task.feed(sleep_ms=period_ms)
                try:
                    v = await Telegram.receive_eval()
                    my_task.out = "Missing bot token" if v is None else f"{v} ({period}s)"
                    cancel_cnt = 0
                except Exception as e:
                    my_task.out = str(e)
                    # Auto scale - blocking nature - in case of serial failures (5) - hibernate task (increase async sleep)
                    cancel_cnt += 1
                    if cancel_cnt > 5:
                        my_task.out = f"[DOWN] {e} (wait 1min)"
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
TELEGRAM_OBJ = None

def __init():
    global TELEGRAM_OBJ
    if TELEGRAM_OBJ is None:
        # ENABLE TELEGRAM IF NW IS STA - CONNECTED TO THE WEB
        _sta_available = True if ifconfig()[0] == "STA" else False
        if _sta_available:
            TELEGRAM_OBJ = Telegram()
        else:
            syslog("No STA: cannot init telegram")

# Auto INIT Telegram at load time (legacy)
__init()

def load():
    """
    Set custom chat commands for Telegram
    - /ping
    - /cmd module function (params)
    """
    __init()
    if TELEGRAM_OBJ is None:
        return "Network unavailable."
    verdict = TELEGRAM_OBJ.set_commands()
    return "Missing telegram bot token" if verdict is None else verdict


def send(text):
    """
    Send Telegram message - micrOS notification
    :param text: text to send
    return verdict
    """
    if TELEGRAM_OBJ is None:
        return "Network unavailable."
    verdict = TELEGRAM_OBJ.send_msg(text)
    return "Missing telegram bot token" if verdict is None else verdict

def notify(text):
    """
    Notify function with system global enable/disable function
    Control with:
        telegram notification enable=True
        telegram notification enable=False
    """
    if TELEGRAM_OBJ is None:
        return "Network unavailable."
    return TELEGRAM_OBJ.notify(text)


def receive():
    """
    Receive Telegram message
    - if all value None, then no incoming messages
    One successful msg receive is necessary to get chat_id for msg send as well!
    """
    if TELEGRAM_OBJ is None:
        return "Network unavailable."
    verdict = TELEGRAM_OBJ.get_msg()
    return "Missing telegram bot token" if verdict is None else verdict


def receiver_loop(period=3):
    """
    Telegram BOT (repl) - ReadEvalPrintLoop for Load Modules
    - Only executes module (function) if the module is already loaded
    :param period: polling period in sec, default: 3
    """
    if TELEGRAM_OBJ is None:
        return "Network unavailable."
    tag = 'telegram.bot_repl'
    state = micro_task(tag=tag, task=TELEGRAM_OBJ.bot_repl(tag=tag, period=period))
    return "Starting" if state else "Already running"


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
            'notify "message"',
            'load', 'INFO: Send & Receive messages with Telegram bot')
