import urequests as requests
from ConfigHandler import cfgget

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

            if resp_json["ok"]:
                if len(resp_json["result"]) > 0:
                    Telegram.CHAT_ID = resp_json["result"][-1]["message"]["chat"]["id"]
                    Telegram.__chat_id_cache('s')
            else:
                Telegram.__chat_id_cache('r')
                if Telegram.CHAT_ID is None:
                    error_message = resp_json.get("description", "Unknown error")
                    raise Exception("Error retrieving chat ID: {}".format(error_message))
        return Telegram.CHAT_ID

    @staticmethod
    def send_msg(text):
        """Send a message to the Telegram chat."""
        bot_token = Telegram.__bot_token()
        if bot_token is None:
            return None
        url = "https://api.telegram.org/bot{}/sendMessage{}".format(bot_token, Telegram.API_PARAMS)
        headers = {"Content-Type": "application/json"}
        data = {"chat_id": Telegram._get_chat_id(), "text": "{}: {}".format(Telegram.DEVFID, text)}
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
            sender, date, text = resp['chat']['username'], resp['date'], resp['text']
            return {'sender': sender, 'date': date, 'text': text}
        else:
            return {'sender': None, 'date': None, 'text': None}
