import urequests as requests
import json
from ConfigHandler import cfgget

#########################################
#          micrOS Notifications         #
#          with Telegram Class          #
#########################################


class Telegram:
    # Telegram bot token and chat ID
    CHAT_ID = None

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
            if bot_token is None:
                return None
            Telegram.CHAT_ID = requests.telegram_chat_id(token=bot_token)
        return Telegram.CHAT_ID

    @staticmethod
    def send_msg(text):
        """Send a message to the Telegram chat."""
        bot_token = Telegram.__bot_token()
        if bot_token is None:
            return None
        url = "https://api.telegram.org/bot{}/sendMessage".format(bot_token)
        headers = {"Content-Type": "application/json"}
        data = {"chat_id": Telegram._get_chat_id(), "text": text}
        response = requests.post(url, headers=headers, json=data)
        return 'Sent' if response.json()['ok'] else response.text

    @staticmethod
    def get_msg():
        """Get the last message from the Telegram chat."""
        bot_token = Telegram.__bot_token()
        if bot_token is None:
            return None
        url = "https://api.telegram.org/bot{}/getUpdates".format(bot_token)
        response = requests.get(url)
        response_json = response.json()
        if len(response_json["result"]) > 0:
            resp = response_json["result"][-1]["message"]
            sender, date, text = resp['chat']['username'], resp['date'], resp['text']
            return {'sender': sender, 'date': date, 'text': text}
        else:
            return {'sender': None, 'date': None, 'text': None}