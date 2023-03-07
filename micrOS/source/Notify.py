from sys import modules
import urequests as requests
from ConfigHandler import cfgget
from TaskManager import exec_lm_core

#########################################
#          micrOS Notifications         #
#          with Telegram Class          #
#########################################


class Telegram:
    # Telegram bot token and chat ID
    # https://core.telegram.org/bots/api
    CHAT_ID = None                                  # Telegram bot chat ID - single group support - persistent caching
    API_PARAMS = "?offset=-1&limit=1&timeout=1"     # Generic API params - optimization
    DEVFID = cfgget('devfid')                       # For reply message (pre text)
    _IN_MSG_ID = None

    @staticmethod
    def __chat_id_cache(mode):
        """
        pds - persistent data structure
        modes:
            r - recover, s - save
        """
        if mode == 's':
            # SAVE CACHE
            with open('telegram.pds', 'w') as f:
                f.write(str(Telegram.CHAT_ID))
            return
        try:
            # RESTORE CACHE
            with open('telegram.pds', 'r') as f:
                Telegram.CHAT_ID = int(f.read().strip())
        except:
            pass

    @staticmethod
    def __bot_token():
        token = cfgget('telegram')
        if token is None or token == 'n/a':
            return None
        return token

    @staticmethod
    def _get_chat_id():
        """Return chat ID or None (in case of no token or cannot get ID)"""
        if Telegram.CHAT_ID is None:
            bot_token = Telegram.__bot_token()
            url = "https://api.telegram.org/bot{}/getUpdates{}".format(bot_token, Telegram.API_PARAMS)
            response = requests.get(url)
            resp_json = response.json()

            if resp_json.get("ok", None) and len(resp_json["result"]) > 0:
                Telegram.CHAT_ID = resp_json["result"][-1]["message"]["chat"]["id"]
                Telegram.__chat_id_cache('s')
            else:
                Telegram.__chat_id_cache('r')
                if Telegram.CHAT_ID is None:
                    error_message = resp_json.get("description", "Unknown error")
                    raise Exception("Error retrieving chat ID: {}".format(error_message))
        return Telegram.CHAT_ID

    @staticmethod
    def send_msg(text, reply_to=None):
        """Send a message to the Telegram chat."""
        bot_token = Telegram.__bot_token()
        if bot_token is None:
            return None
        url = "https://api.telegram.org/bot{}/sendMessage{}".format(bot_token, Telegram.API_PARAMS)
        headers = {"Content-Type": "application/json"}
        data = {"chat_id": Telegram._get_chat_id(), "text": "{}: {}".format(Telegram.DEVFID, text)}
        if isinstance(reply_to, int):
            data['reply_to_message_id'] = reply_to
            Telegram._IN_MSG_ID = reply_to
        response = requests.post(url, headers=headers, json=data)
        return 'Sent' if response.json()['ok'] else response.text

    @staticmethod
    def get_msg():
        """Get the last message from the Telegram chat."""
        bot_token = Telegram.__bot_token()
        if bot_token is None:
            return None
        url = "https://api.telegram.org/bot{}/getUpdates{}".format(bot_token, Telegram.API_PARAMS)
        response = requests.get(url)
        response_json = response.json()
        if len(response_json["result"]) > 0:
            resp = response_json["result"][-1]["message"]
            sender, date, text, m_id = resp['chat']['username'], resp['date'], resp['text'], resp['message_id']
            return {'sender': sender, 'date': date, 'text': text, 'm_id': m_id}
        else:
            return {'sender': None, 'date': None, 'text': None, 'm_id': -1}

    @staticmethod
    def receive_eval():
        out = {"out": "", "verdict": None}

        def out_msg(msg):
            out['out'] += msg

        data = Telegram.get_msg()
        msg_in, m_id = data['text'], data['m_id']
        if msg_in is not None and m_id != Telegram._IN_MSG_ID:
            loaded_mods = [lm.replace('LM_', '') for lm in modules.keys() if lm.startswith('LM_')]
            # PING - Get auto reply from node - loaded modules
            if msg_in.startswith('/ping'):
                Telegram.send_msg(', '.join(loaded_mods), reply_to=m_id)
            # CMD - Load Module execution handling
            elif msg_in.startswith('/cmd'):
                cmd_lm = msg_in.replace('/cmd', '').strip().split()
                if cmd_lm[0] in loaded_mods:
                    out['verdict'] = f'Exec: {" ".join(cmd_lm)}'
                    try:
                        exec_lm_core(cmd_lm, msgobj=out_msg)
                    except Exception as e:
                        out_msg(str(e))
                    Telegram.send_msg(out['out'], reply_to=m_id)
                else:
                    out['verdict'] = f'NoAccess: {cmd_lm[0]}'
        else:
            out['verdict'] = f"NoExec: {msg_in}"
        return out['verdict']
