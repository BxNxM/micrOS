import json
from utime import ticks_ms
from mqtt_as import MQTTClient, config
from Config import cfgget
from Common import micro_task, console, syslog
from Notify import Notify


class MQTT(Notify):
    INSTANCE = None

    QOS: int = None
    DEBUG: bool = True
    DEFAULT_TOPIC: str = "micros/#"

    # Micro Task TGS
    SUB_TASK = 'mqtt.subscribe'
    UNSUB_TASK = 'mqtt.unsubscribe'
    CLIENT_TASK = 'mqtt.client'
    UP_TASK = 'mqtt.up'

    def __new__(cls, *args, **kwargs):
        if cls.INSTANCE is None:
            # Create and store the instance
            cls.INSTANCE = super().__new__(cls)
        return cls.INSTANCE

    def __init__(self):
        # Init should only run once — guard it
        if getattr(self, "_initialized", False):
            return
        super().add_subscriber(self)
        self.client:MQTTClient = None
        MQTT.DEFAULT_TOPIC = f"{self._DEVFID}/#"
        self._initialized = True

    def init_client(self, username, password, server_ip, server_port):
        """
        Build the MQTT client configuration.
        :param username: Broker username
        :param password: Broker password.
        :param server_ip: Broker IP or hostname.
        :param server_port: Broker port.
        :return: MQTT instance and Updated configuration dictionary.
        """
        config.update({
            'client_id': self._DEVFID,
            'server': server_ip,
            'port': server_port,
            'user': username,
            'password': password,
            'ssid': cfgget("staessid"),  # Only supports a single Wi-Fi connection. Multiple SSIDs not handled.
            'wifi_pw': cfgget("stapwd"),
            'keepalive': 120,
            'queue_len': 1,  # Use event interface with default queue
            'will': (f'{self._DEVFID}/status', '{"status": "offline"}', True, 1)
        })
        self.client = MQTTClient(config)
        return self.client, config

    async def run_receiver(self):
        """
        Initialize and connect the MQTT client, subscribe to default topics,
        start up-listener, and begin receiving messages.
        """
        with micro_task(tag=MQTT.CLIENT_TASK) as my_task:
            try:
                await self.client.connect()
                my_task.out = "Connection successful."
            except OSError:
                my_task.out = "Connection failed."
                return

            # Wait for mqtt client connected successfully
            await self.client.up.wait()
            self.client.up.clear()

            # Initialize mqtt topics
            try:
                micro_task(tag=MQTT.SUB_TASK, task=self._subscribe(MQTT.DEFAULT_TOPIC))
            except Exception as err:
                syslog(f"Failed start mqtt subscribe: {err}")
            try:
                micro_task(tag=MQTT.UP_TASK, task=self._up())
            except Exception as err:
                syslog(f"Failed start mqtt up: {err}")
            # Async listener loop
            await self._receiver()
            my_task.out = "Receiver closed"

        # Close when listener exits
        self.client.close()

    @staticmethod
    def send_msg(text, *args, **kwargs):
        """
        Notify callback method interface
        :param text: text message to send
        :param topic: topic to use (default: None -> use default topic)
        """
        dev_id = MQTT.INSTANCE._DEVFID
        topic = kwargs.get("topic", args[0] if len(args) > 0 else None)
        topic = dev_id if topic is None else f"{dev_id}/{topic}"
        return MQTT().publish(topic=topic, message=text, retain=False)

    #############################
    # SUBSCRIPTION \ PUBLISHING #
    #############################

    async def _unsubscribe(self, topic: str):
        """
        Unsubscribe from the specified MQTT topic.
        :param topic: Topic string to unsubscribe from.
        """
        with micro_task(tag=MQTT.UNSUB_TASK) as my_task:
            my_task.out = "Started"
            try:
                console(f"Unsubscribe topic: {topic}")
                await self.client.unsubscribe(topic)
                my_task.out = "Done"
            except Exception as e:
                my_task.out = f"Error: {e}"

    async def _subscribe(self, topic: str):
        """
        Subscribe to the specified MQTT topic with the global QoS.
        :param topic: Topic string to subscribe to.
        """
        with micro_task(tag=MQTT.SUB_TASK) as my_task:
            my_task.out = "Started"
            try:
                console(f"Subscribe topic: {topic}")
                await self.client.subscribe(topic, qos=MQTT.QOS)
                my_task.out = "Done"
            except Exception as e:
                my_task.out = f"Error: {e}"

    @staticmethod
    async def _publish(tag, message: str, topic: str, retain: bool):
        """
        Asynchronously publish a message to the given MQTT topic.
        :param message: The message payload as a string.
        :param topic: The MQTT topic string.
        :param retain: Whether the message should be retained on the broker.
        """
        with micro_task(tag) as my_task:
            my_task.out = f"Publishing {topic}"
            await MQTT().client.publish(topic, message, qos=MQTT.QOS, retain=retain)
            my_task.out = f"Publish {topic} done"

    def _publish_error(self, topic: str, error_msg: str):
        """
        Publish an error message to the <topic>/response MQTT topic and log it to the console.
        :param topic: The original MQTT topic where the error occurred.
        :param error_msg: The error message string.
        """
        self.publish(topic=f"{topic}/response", message=error_msg)
        console(error_msg)

    @staticmethod
    def publish(topic: str, message: str, retain: bool = False):
        """
        Wrapper to publish a message to the specified topic.
        Creates a micro_task for asynchronous publishing.
        :param topic: MQTT topic string.
        :param message: Message string.
        :param retain: Whether to retain the message on the broker (default False).
        :return: Status message string.
        """
        unique_tag = f'mqtt.publish.{topic}.{ticks_ms()}'

        if len(topic.split('/')) == 3:
            console(
                "Error: Topic cannot consist of exactly three parts, as such topics are interpreted as executable commands.")
            return "Error: Topic cannot consist of exactly three parts, as such topics are interpreted as executable commands."

        state: dict = micro_task(tag=unique_tag, task=MQTT()._publish(unique_tag, message, topic, retain))
        return f"Message was sent ({list(state.values())[0]})"

    async def _receiver(self):
        """
        Asynchronous loop that listens for incoming MQTT messages from the subscribed topics.
        - Decodes topic and message.
        - Validates JSON payload, runs commands via Notify.lm_execute, and publishes a JSON-formatted response.
        """
        async for topic, msg, retained in self.client.queue:
            incoming_topic, msg = topic.decode(), msg.decode()
            console(f'Topic: "{incoming_topic}" Message: "{msg}" Retained: {retained}')

            topic_parts = incoming_topic.split('/')
            if len(topic_parts) == 3:
                payload = {}
                if msg.strip():
                    try:
                        payload = json.loads(msg)
                    except ValueError:
                        self._publish_error(incoming_topic, f"Invalid payload JSON on topic {incoming_topic}: {msg}")
                        continue

                args = [f'{k}="{v}"' if isinstance(v, str) else f'{k}={v}' for k, v in payload.items()]

                cmd_parts = topic_parts[1:] + args

                state, output_json = self.lm_execute(cmd_parts, jsonify=True, secure=False)
                try:
                    output = json.loads(output_json)
                except ValueError:
                    output = output_json

                resp_payload = json.dumps({"state": state, "result": output})
                self.publish(topic=f"{incoming_topic}/response", message=resp_payload)

    async def _up(self):
        """
        CLIENT LIFECYCLE
        UP Listener task that waits for an MQTT 'up' event (reconnection) and re-subscribes to the default topic.
        """
        with micro_task(tag=MQTT.UP_TASK) as my_task:
            while True:
                # Wait for UP Event - (re)subscribe
                my_task.out = "Wait"
                await self.client.up.wait()
                self.client.up.clear()
                state:dict = micro_task(tag=MQTT.SUB_TASK, task=self._subscribe(MQTT.DEFAULT_TOPIC))
                my_task.out = f"Re-Subscription ({list(state.values())[0]})"
                my_task.feed()

#############################
#       Public functions    #
#############################


def load(username:str, password:str, server_ip:str, server_port:str='1883', qos:int=1):
    """
    Configure, initialize, and start the MQTT client.
    Requires that the micropython-mqtt package is installed. You can install it with:
    mpremote mip install github:peterhinch/micropython-mqtt
    :param username: Broker username.
    :param password: Broker password.
    :param server_ip: Broker IP or hostname.
    :param server_port: MQTT port (default 1883).
    :param qos: MQTT Quality of Service level (0, 1, or 2). Controls delivery guarantee.
    :return: Status dict showing whether the client is starting or already running.
    """
    MQTTClient.DEBUG = MQTT.DEBUG
    MQTT.QOS = qos
    inst = MQTT()
    inst.init_client(username, password, server_ip, server_port)
    return micro_task(tag=MQTT.CLIENT_TASK, task=inst.run_receiver())


def publish(topic:str, message:str, retain=False):
    """
    Publish a message to the specified topic.
    :param topic: MQTT topic string.
    :param message: Message string.
    :param retain: Whether to retain the message on the broker (default False).
    :return: Status message string.
    """
    return MQTT().publish(topic, message, retain)


def get_config():
    """
    Get configuration for MQTT client.
    :return: MQTT configuration dict.
    """
    return config


def help(widgets=False):
    """
    Show public functions. Return a tuple of public function usage strings for the MQTT module.
    :param widgets: Unused, reserved for extra help formatting.
    :return: Tuple of help strings.
    """
    return ('load username:str password:str server_ip:str server_port:str="1883"',
            'get_config',
            'publish topic:str message:str retain=False')
