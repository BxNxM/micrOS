import uasyncio as asyncio
from Notify import Telegram
from Common import micro_task, syslog
from Network import ifconfig

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


async def __task():
    cancel_cnt = 0
    with micro_task(tag='telegram._loop') as my_task:
        my_task.out = "[UP] Running"
        while True:
            # Normal task period
            await asyncio.sleep(5)
            try:
                v = TELEGRAM_OBJ.receive_eval()
                my_task.out = "Missing bot token" if v is None else v
                cancel_cnt = 0
            except Exception as e:
                my_task.out = str(e)
                # Auto scale - blocking nature - in case of serial failures (5) - hibernate task (increase async sleep)
                cancel_cnt += 1
                if cancel_cnt > 5:
                    my_task.out = f"[DOWN] {e}"
                    cancel_cnt = 5
                    # SLOW DOWN - hibernate task
                    asyncio.sleep(115)


def receiver_loop():
    """
    Telegram msg receiver loop - automatic LM execution
    - Only executes module (function) if the module is already loaded
    on the endpoint / micrOS node
    """
    if TELEGRAM_OBJ is None:
        return "Network unavailable."
    state = micro_task(tag='telegram._loop', task=__task())
    return "Starting" if state else "Already running"


def notifications(enable=None):
    """
    Global notifications control for micrOS
    :param enable: True: Enable notifications / False: Disable notifications
    return: state verdict
    """
    if enable is None:
        enable = not Telegram.GLOBAL_NOTIFY
    return Telegram.notifications(state=enable)


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return ('send "text"',
            'receive',
            'receiver_loop',
            'notify "message"',
            'notifications enable=False',
            'load', 'INFO: Send & Receive messages with Telegram bot')
