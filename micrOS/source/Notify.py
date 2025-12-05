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
        :param channels (optional): select communication interface(s) by class name
               e.g. "Telegram", "MQTT" or an iterable of these.
               If omitted or empty, sends over all available channels.
        Telegram params (optional):
            reply_to: message id to reply to (optional) - default: None
             chat_id: chat identifier - default: None -> auto resolve in child class
        MQTT client params (optional):
            topic: mqtt topic to send the message - default: None -> auto resolve in child class
        return: verdict and metrics
        """
        errors, channels, interfaces = 0, kwargs.get("channels", ()), set()
        channels = (channels,) if isinstance(channels, str) else tuple(channels)
        for s in Notify._SUBSCRIBERS:
            name = s.__class__.__name__
            try:
                if len(channels) == 0 or name in channels:
                    s.send_msg(text, *args, **kwargs)
                    interfaces.add(name)
            except Exception as e:
                syslog(f"[ERR] Notify.{name}: {e}")
                errors+=1
        return (f"Sent over {', '.join(interfaces)} ({len(interfaces)}/{len(Notify._SUBSCRIBERS)}) client(s)"
                f" - errors: ({errors})")

    @staticmethod
    def notifications(state=None):
        """
        Setter for disable/enable notification messages (over LM_system)
        :param state: True/False/ None(default) - show current state
        """
        if isinstance(state, bool):
            Notify.GLOBAL_NOTIFY = state
        targets = ", ".join(s.__class__.__name__ for s in Notify._SUBSCRIBERS)
        return f"Notifications[{targets}]: {'enabled' if Notify.GLOBAL_NOTIFY else 'disabled'}"

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
