import uasyncio as asyncio
from Notify import Telegram
from Common import micro_task

#########################################
#          micrOS Notifications         #
#########################################

TELEGRAM_OBJ = Telegram()


def load_n_init():
    """Set custom chat commands for Telegram"""
    if TELEGRAM_OBJ is None:
        return "No telegram token available"
    return TELEGRAM_OBJ.set_commands()


def send(text):
    """
    Send Telegram message
    :param text: text to send
    return verdict
    """
    verdict = TELEGRAM_OBJ.send_msg(text)
    if verdict is None:
        return "Telegram not available,\ncheck your bot token or try later..."
    return verdict


def receive():
    """
    Receive Telegram message
    - if all value None, then no incoming messages
    One successful msg receive is necessary to get chat_id for msg send as well!
    """
    verdict = TELEGRAM_OBJ.get_msg()
    if verdict is None:
        return "Telegram not available, \ncheck your bot token or try later..."
    return verdict


async def __task():
    with micro_task(tag='telegram._lm_loop') as my_task:
        while True:
            try:
                my_task.out = TELEGRAM_OBJ.receive_eval()
            except Exception as e:
                my_task.out = str(e)
            await asyncio.sleep(5)


def lm_loop():
    """
    Telegram msg receiver loop - automatic execution [beta]
    """
    if TELEGRAM_OBJ is None:
        return "Cannot start, no telegram token."
    state = micro_task(tag='telegram._lm_loop', task=__task())
    return "Starting" if state else "Already running"


def help():
    return 'send "text"', 'receive', 'lm_loop', 'load_n_init', 'INFO: Send & Receive messages with Telegram bot'
