import uasyncio as asyncio
from Notify import Telegram
from Common import micro_task
from Network import ifconfig

#########################################
#          micrOS Notifications         #
#########################################

# ENABLE TELEGRAM IF NW IS STA - CONNECTED TO THE WEB
_ENABLE = True if ifconfig()[0] == "STA" else False
if _ENABLE:
    TELEGRAM_OBJ = Telegram()
    if TELEGRAM_OBJ.__bot_token() is None:
        # NO TELEGRAM TOKEN
        TELEGRAM_OBJ = None
else:
    # NO NETWORK CONNECTION (STA)
    TELEGRAM_OBJ = None


def load_n_init():
    """
    Set custom chat commands for Telegram
    - /ping
    - /cmd module function (params)
    """
    if TELEGRAM_OBJ is None:
        return "No telegram token OR network connection."
    return TELEGRAM_OBJ.set_commands()


def send(text):
    """
    Send Telegram message - micrOS notification
    :param text: text to send
    return verdict
    """
    if TELEGRAM_OBJ is None:
        return "No telegram token OR network connection."
    verdict = TELEGRAM_OBJ.send_msg(text)
    if verdict is None:
        return "Telegram not available."
    return verdict


def receive():
    """
    Receive Telegram message
    - if all value None, then no incoming messages
    One successful msg receive is necessary to get chat_id for msg send as well!
    """
    if TELEGRAM_OBJ is None:
        return "No telegram token OR network connection."
    verdict = TELEGRAM_OBJ.get_msg()
    if verdict is None:
        return "Telegram not available."
    return verdict


async def __task():
    with micro_task(tag='telegram._lm_loop') as my_task:
        while True:
            try:
                my_task.out = TELEGRAM_OBJ.receive_eval()
            except Exception as e:
                my_task.out = str(e)
            await asyncio.sleep(5)


def receiver_loop():
    """
    Telegram msg receiver loop - automatic LM execution
    - Only executes module (function) if the module is already loaded
    on the endpoint / micrOS node
    """
    if TELEGRAM_OBJ is None:
        return "No telegram token OR network connection."
    state = micro_task(tag='telegram._lm_loop', task=__task())
    return "Starting" if state else "Already running"


def help():
    return 'send "text"', 'receive', 'receiver_loop', 'load_n_init', 'INFO: Send & Receive messages with Telegram bot'
