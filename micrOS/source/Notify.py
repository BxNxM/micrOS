"""
Module is responsible for Notification handling
Common:
    - notifications None/True/False
    - notify 'text'
    - lm_execute
Supported notification subscribers (add_subscriber)
    - LM_telegram
Designed by Marcell Ban aka BxNxM
"""

from Config import cfgget
from Tasks import lm_exec, lm_is_loaded
from Debug import errlog_add

#########################################
#          micrOS Notifications         #
#          with Telegram Class          #
#########################################
class Notify:
    GLOBAL_NOTIFY = True            # Enable Global notifications
    _DEVFID = cfgget('devfid')      # For reply message (pre text)
    _SUBSCRIBERS = set()            # Store set of notification objects: send_msg

    @staticmethod
    def add_subscriber(instance):
        """
        Add Notification agent like: Telegram
        """
        if isinstance(instance, Notify):
            Notify._SUBSCRIBERS.add(instance)
            return True
        raise Exception("Subscribe error, Notify parent missing")

    @staticmethod
    def send_msg(text, reply_to=None, chat_id=None):
        raise NotImplementedError("Child class must implement send_msg method")

    @staticmethod
    def message(text, reply_to=None, chat_id=None):
        """
        Send message to all subscribers - Notify agents
        """
        exit_code = 0
        for s in Notify._SUBSCRIBERS:
            try:
                # !!! SUBSCRIBER HAS TO DEFINE send_msg(text, reply_to, chat_id) method !!!
                s.send_msg(text, reply_to, chat_id)
            except Exception as e:
                errlog_add(f"[ERR] Notify: {e}")
                exit_code+=1
        return f"Sent for {len(Notify._SUBSCRIBERS)} client(s), errors: ({exit_code})"

    @staticmethod
    def notifications(state=None):
        """
        Setter for disable/enable notification messages
        """
        if isinstance(state, bool):
            Notify.GLOBAL_NOTIFY = state
        return f"Notifications: {'enabled' if Notify.GLOBAL_NOTIFY else 'disabled'}"

    @staticmethod
    def notify(text, reply_to=None, chat_id=None):
        """
        Notification sender
        """
        if Notify.GLOBAL_NOTIFY:
            return Notify.message(text, reply_to, chat_id)
        return "Notifications disabled"

    @staticmethod
    def lm_execute(cmd_args):
        """Load Module Executor with basic access handling"""
        if lm_is_loaded(cmd_args[0]):
            try:
                _, out = lm_exec(cmd_args)
            except Exception as e:
                out = str(e)
            return True, out
        return False, cmd_args[0]
