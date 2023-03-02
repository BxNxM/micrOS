from Notify import Telegram

#########################################
#          micrOS Notifications         #
#########################################

TELEGRAM_OBJ = Telegram()


def send(text):
    verdict = TELEGRAM_OBJ.send_msg(text)
    if verdict is None:
        return "Telegram not available,\ncheck your bot token or try later..."
    return verdict


def receive():
    verdict = TELEGRAM_OBJ.get_msg()
    if verdict is None:
        return "Telegram not available, \ncheck your bot token or try later..."
    return verdict


def help():
    return 'send "text"', 'receive', 'INFO: Send & Receive messages with Telegram bot'
