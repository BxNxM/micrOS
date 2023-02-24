from Notify import Telegram

#########################################
#          micrOS Notifications         #
#########################################


def send(text):
    verdict = Telegram.send_msg(text)
    if verdict is None:
        return "Telegram not available,\ncheck your bot token or try later..."
    return verdict


def receive():
    verdict = Telegram.get_msg()
    if verdict is None:
        return "Telegram not available, \ncheck your bot token or try later..."
    return verdict


def help():
    return 'send "text"', 'receive', 'INFO: Send & Receive messages with Telegram bot'
