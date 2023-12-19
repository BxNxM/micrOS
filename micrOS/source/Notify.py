from sys import modules
import urequests
from ConfigHandler import cfgget
from TaskManager import exec_lm_core
from Debug import console_write
import binascii # TODO: photo read...

#########################################
#          micrOS Notifications         #
#          with Telegram Class          #
#########################################


class Telegram:
    # Telegram bot token and chat ID
    # https://core.telegram.org/bots/api
    _TOKEN = None
    _CHAT_IDS = set()                                # Telegram bot chat IDs - multi group support - persistent caching
    _API_PARAMS = "?offset=-1&limit=1&timeout=2"     # Generic API params - optimization
    _DEVFID = cfgget('devfid')                       # For reply message (pre text)
    _IN_MSG_ID = None

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
    def send_msg(data, reply_to=None, chat_id=None, dtype='text'):
        """
        Send a message to the Telegram chat by chat_id
        :param data: send text (dtype) OR other data types like photo...
        :param reply_to: reply to specific message, if None, simple reply
        :param chat_id: chat_id to reply on, if None, reply to all known
        :param dtype: data type to send back: text OR photo
        RETURN None when telegram bot token is missing
        """
        def _send(chat):
            """Send message to chat_id (chat)"""
            _data = {"chat_id": chat, dtype: f"{Telegram._DEVFID}⚙️\n{data}" if dtype == 'text' else data}
            if isinstance(reply_to, int):
                _data['reply_to_message_id'] = reply_to
                Telegram._IN_MSG_ID = reply_to
            print(f"_______SEND: {_data}")
            _, _resp = urequests.post(url, headers={"Content-Type": "application/json"}, json=_data, jsonify=True, sock_size=128)
            console_write(f"\tSend {dtype}:\n{_data}\nresponse:\n{_resp}")
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

        # Supported telegram endpoints: sendMessage(text) AND sendPhoto(photo)
        endpoint= f'sendMessage{Telegram._API_PARAMS}' if dtype == 'text' else 'sendPhoto'
        url = f"https://api.telegram.org/bot{bot_token}/{endpoint}"
        console_write(f"[TELEGRAM] API: {url}")

        verdict = ""
        # Reply to ALL (notification) - chat_id was not provided
        if chat_id is None:
            console_write("\tREPLY ALL")
            for _chat_id in _get_chat_ids():
                resp_json = _send(chat=_chat_id)
                verdict += f'Sent{_chat_id};' if resp_json['ok'] else str(resp_json)
        else:
            console_write(f"\tREPLY TO {chat_id}")
            # Direct reply to chat_id
            resp_json = _send(chat=chat_id)
            verdict = f'Sent{chat_id}' if resp_json['ok'] else str(resp_json)
        return verdict

    @staticmethod
    def get_msg():
        """
        Get the last message from the Telegram chat.
        RETURN None when telegram bot token is missing
        """

        def _update_chat_ids():
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

        # --------------------- FUNCTION MAIN ------------------------ #
        console_write("[NTFY] GET MESSAGE")
        bot_token = Telegram.__bot_token()
        if bot_token is None:
            return None
        response = {'sender': None, 'text': None, 'm_id': -1, 'c_id': None}
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates{Telegram._API_PARAMS}"
        console_write(f"\t1/2[GET] request: {url}")
        _, resp_json = urequests.get(url, jsonify=True, sock_size=128)
        if len(resp_json["result"]) > 0:
            response['c_id'] = _update_chat_ids()
            resp = resp_json["result"][-1]["message"]
            response['sender'] = f"{resp['chat']['first_name']}{resp['chat']['last_name']}" if resp['chat'].get('username', None) is None else resp['chat']['username']
            response['text'], response['m_id'] = resp['text'], resp['message_id']
        console_write(f"\t2/2[GET] response: {response}")
        return response

    @staticmethod
    def receive_eval():
        """
        READ - VALIDATE - EXECUTE - REPLY LOOP
        - can be used in async loop
        RETURN None when telegram bot token is missing
        """

        console_write("[NTFY] REC&EVAL sequence")

        # Return data structure template
        verdict = None
        out = ""

        # exec_lm_core msg object definition
        def out_msg(msg):
            nonlocal out
            out += msg

        def lm_execute(cmd_args):
            nonlocal verdict
            if cmd_args[0] in loaded_mods:
                verdict = f'[UP] Exec: {" ".join(cmd_args[0])}'
                try:
                    exec_lm_core(cmd_args, msgobj=out_msg)
                except Exception as e:
                    out_msg(str(e))
                Telegram.send_msg(out, reply_to=m_id)
            else:
                verdict = f'[UP] NoAccess: {cmd_args[0]}'
                Telegram._IN_MSG_ID = m_id

        # -------------------------- FUNCTION MAIN -------------------------- #
        # Poll telegram chat
        data = Telegram.get_msg()
        if data is None:
            return data
        # Get msg, msg_id, chat_id as main input data source
        msg_in, m_id, c_id = data['text'], data['m_id'], data['c_id']
        if msg_in is not None and m_id != Telegram._IN_MSG_ID:
            # replace single/double quotation to apostrophe (str syntax for repl interpretation)
            msg_in = msg_in.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"')
            # Parse loaded modules
            loaded_mods = [lm.replace('LM_', '') for lm in modules.keys() if lm.startswith('LM_')]
            loaded_mods.append('task')      # add task "module" to whitelist
            # [TELEGRAM CMD] /PING - Get auto reply from node - loaded modules
            #               Example: /ping
            if msg_in.startswith('/ping'):
                Telegram.send_msg(', '.join(loaded_mods), reply_to=m_id, chat_id=c_id)
            # [TELEGRAM CMD] /CMD_SELECT - Load Module execution handling - SELECTED DEV. MODE
            #               Example: /cmd_select device module func param(s)
            elif msg_in.startswith('/cmd_select'):
                cmd_lm = msg_in.replace('/cmd_select', '').strip().split()
                # [Compare] cmd selected device param with DEVFID (device/prompt name)
                if cmd_lm[0] in Telegram._DEVFID:
                    lm_execute(cmd_lm[1:])
                else:
                    verdict = f'[UP] NoSelected: {cmd_lm[0]}'
            # [TELEGRAM CMD] /CMD - Load Module execution handling - ALL mode
            #               Example: /cmd module func param(s)
            elif msg_in.startswith('/cmd'):
                cmd_lm = msg_in.replace('/cmd', '').strip().split()
                lm_execute(cmd_lm)
            elif msg_in.startswith('/photo'):
                #TODO - photo reply - check LM_OV2640 was loaded + capture
                #Telegram.send_msg('HelloBello: <photo>', reply_to=m_id, chat_id=c_id)
                try:
                    with open('photo.jpg', 'rb') as p:
                        #image_data = binascii.b2a_base64(p.read()).decode('utf-8').strip()
                        image_data = p.read()
                        Telegram.send_msg(image_data, reply_to=m_id, chat_id=c_id, dtype='photo')
                except Exception as e:
                    Telegram.send_msg(str(e), reply_to=m_id, chat_id=c_id)
        else:
            verdict = "[UP] NoExec"
        console_write(f"\tREC&EVAL: {verdict}")
        return verdict

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
        data = {"commands": [{"command": "ping", "description": "Ping All endpoints, return active modules."},
                             {"command": "cmd", "description": "Command to All endpoints (only loaded modules)."},
                             {"command": "cmd_select", "description": "Command to Selected endpoints: device module func"},
                             {"command": "photo", "description": "Get OV2640 camera image."},
                             ]}
        _, resp_json = urequests.post(url, headers={"Content-Type": "application/json"}, json=data, jsonify=True, sock_size=128)
        return 'Custom commands was set' if resp_json['ok'] else str(resp_json)
