"""
Module is responsible for Notification handling
Common:
    - notifications None/True/False
    - notify 'text'
    - lm_execute
Supported notification subscribers (add_subscriber)
    - LM_telegram
    - LM_mqtt_client
Designed by Marcell Ban aka BxNxM
"""

from Config import cfgget
from Tasks import lm_exec, lm_is_loaded
from Debug import syslog

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
    def send_msg(text, *args, **kwargs):
        """
        This method has to be implemented by the child class
        """
        raise NotImplementedError("Child class must implement send_msg method")

    @staticmethod
    def message(text, *args, **kwargs):
        """
        Send message to all subscribers - Notify send_msg(text, ...) agents
        :param text: text message to send
        Telegram params:
            reply_to: message id to reply to (optional) - default: None
             chat_id: chat identifier - default: None -> auto resolve in child class
        MQTTClient params:
            topic: mqtt topic to send the message - default: None -> auto resolve in child class
        """
        exit_code = 0
        for s in Notify._SUBSCRIBERS:
            try:
                s.send_msg(text, *args, **kwargs)
            except Exception as e:
                syslog(f"[ERR] Notify: {e}")
                exit_code+=1
        return f"Sent for {len(Notify._SUBSCRIBERS)} client(s), errors: ({exit_code})"

    @staticmethod
    def notifications(state=None):
        """
        Setter for disable/enable notification messages (over LM_system)
        """
        if isinstance(state, bool):
            Notify.GLOBAL_NOTIFY = state
        return f"Notifications: {'enabled' if Notify.GLOBAL_NOTIFY else 'disabled'}"

    @staticmethod
    def notify(text, *args, **kwargs):
        """
        Notification sender for Load Modules
        """
        if Notify.GLOBAL_NOTIFY:
            return Notify.message(text, *args, **kwargs)
        return "Notifications disabled"

    @staticmethod
    def lm_execute(cmd_args, jsonify=False, secure=True):
        """Load Module Executor with basic access handling"""
        state = False
        if secure and not lm_is_loaded(cmd_args[0]):
            return state, f"NotAllowed {cmd_args[0]}"
        try:
            state, out = lm_exec(cmd_args, jsonify)
        except Exception as e:
            out = str(e)
        return state, out
