import json
import time
from mqtt_as import MQTTClient, config
from Config import cfgget
from Common import micro_task, console, syslog, exec_cmd


class MQTT:
    CLIENT:MQTTClient = None        # MQTT Client (broker) instance
    QOS: int = None
    DEBUG: bool = True
    DEFAULT_TOPIC: str = f"{cfgget('devfid')}/#"

    # Micro Task TGS
    SUB_TASK = 'mqtt.subscribe'
    UNSUB_TASK = 'mqtt.unsubscribe'
    CLIENT_TASK = 'mqtt.client'
    UP_TASK = 'mqtt.up'


######################
# CORE MQTT HANDLERS #
######################


async def _receiver():
    """
    Asynchronous loop that listens for incoming MQTT messages from the subscribed topics.
    - Decodes topic and message.
    - Validates JSON payload, runs commands via exec_cmd, and publishes a JSON-formatted response.
    """
    async for topic, msg, retained in MQTT.CLIENT.queue:
        incoming_topic, msg = topic.decode(), msg.decode()
        console(f'Topic: "{incoming_topic}" Message: "{msg}" Retained: {retained}')

        topic_parts = incoming_topic.split('/')
        if len(topic_parts) == 3:
            payload = {}
            if msg.strip():
                try:
                    payload = json.loads(msg)
                except ValueError:
                    _publish_error(incoming_topic, f"Invalid payload JSON on topic {incoming_topic}: {msg}")
                    continue

            args = [f'{k}="{v}"' if isinstance(v, str) else f'{k}={v}' for k, v in payload.items()]
            
            cmd_parts = topic_parts[1:] + args

            state, output_json = exec_cmd(cmd=cmd_parts, jsonify=True)
            try:
                output = json.loads(output_json)
            except ValueError:
                output = output_json

            resp_payload = json.dumps({"state": state, "result": output})
            publish(topic=f"{incoming_topic}/response", message=resp_payload)


def _publish_error(topic: str, error_msg: str):
    """
    Publish an error message to the <topic>/response MQTT topic and log it to the console.
    :param topic: The original MQTT topic where the error occurred.
    :param error_msg: The error message string.
    """
    publish(topic=f"{topic}/response", message=error_msg)
    console(error_msg)


#############################
# SUBSCRIPTION \ PUBLISHING #
#############################


async def _unsubscribe(topic: str):
    """
    Unsubscribe from the specified MQTT topic.
    :param topic: Topic string to unsubscribe from.
    """
    with micro_task(tag=MQTT.UNSUB_TASK) as my_task:
        my_task.out = "Started"
        try:
            console(f"Unsubscribe topic: {topic}")
            await MQTT.CLIENT.unsubscribe(topic)
            my_task.out = "Done"
        except Exception as e:
            my_task.out = f"Error: {e}"


async def _subscribe(topic: str):
    """
    Subscribe to the specified MQTT topic with the global QoS.
    :param topic: Topic string to subscribe to.
    """
    with micro_task(tag=MQTT.SUB_TASK) as my_task:
        my_task.out = "Started"
        try:
            console(f"Subscribe topic: {topic}")
            await MQTT.CLIENT.subscribe(topic, qos=MQTT.QOS)
            my_task.out = "Done"
        except Exception as e:
            my_task.out = f"Error: {e}"


async def _publish(message: str, topic: str, retain: bool):
    """
    Asynchronously publish a message to the given MQTT topic.
    :param message: The message payload as a string.
    :param topic: The MQTT topic string.
    :param retain: Whether the message should be retained on the broker.
    """
    await MQTT.CLIENT.publish(topic, message, qos=MQTT.QOS, retain=retain)


def publish(topic: str, message: str, retain: bool = False):
    """
    Wrapper to publish a message to the specified topic.
    Creates a micro_task for asynchronous publishing.
    :param topic: MQTT topic string.
    :param message: Message string.
    :param retain: Whether to retain the message on the broker (default False).
    :return: Status message string.
    """
    unique_tag = f'mqtt.publish.{topic}.{time.ticks_ms()}'

    if len(topic.split('/')) == 3:
        console("Error: Topic cannot consist of exactly three parts, as such topics are interpreted as executable commands.")
        return "Error: Topic cannot consist of exactly three parts, as such topics are interpreted as executable commands."

    state = micro_task(tag=unique_tag, task=_publish(message, topic, retain))
    return f"Message was sent {state}"


####################
# CLIENT LIFECYCLE #
####################


async def _up():
    """
    UP Listener task that waits for an MQTT 'up' event (reconnection) and re-subscribes to the default topic.
    """
    with micro_task(tag=MQTT.UP_TASK) as my_task:
        while True:
            # Wait for UP Event - (re)subscribe
            my_task.out = "Wait"
            await MQTT.CLIENT.up.wait()
            MQTT.CLIENT.up.clear()
            state = micro_task(tag=MQTT.SUB_TASK, task=_subscribe(MQTT.DEFAULT_TOPIC))
            my_task.out = f"Re-Subscription {state}"
            my_task.feed()


async def _init_client():
    """
    Initialize and connect the MQTT client, subscribe to default topics, 
    start up-listener, and begin receiving messages.
    """
    with micro_task(tag=MQTT.CLIENT_TASK) as my_task:
        try:
            await MQTT.CLIENT.connect()
            my_task.out = "Connection successful."
        except OSError:
            my_task.out = "Connection failed."
            return

        # Wait for mqtt client connected successfully
        await MQTT.CLIENT.up.wait()
        MQTT.CLIENT.up.clear()
        
        # Initialize mqtt topics
        if not micro_task(tag=MQTT.SUB_TASK, task=_subscribe(MQTT.DEFAULT_TOPIC)):
            syslog(f"Failed start mqtt subscribe: {state}")
        if not micro_task(tag=MQTT.UP_TASK, task=_up()):
            syslog(f"Failed start mqtt up: {state}")

        # Async listener loop
        await _receiver()
        my_task.out = "Receiver closed"

    # Close when listener exits
    MQTT.CLIENT.close()


#################
# CONFIGURATION #
#################


def get_config():
    """
    Get configuration for MQTT client.
    :return: MQTT configuration dict.
    """
    return config


def _configure(username: str, password: str, server_ip: str, server_port: str):
    """
    Build the MQTT client configuration.
    :param username: Broker username.
    :param password: Broker password.
    :param server_ip: Broker IP or hostname.
    :param server_port: Broker port.
    :return: Updated configuration dictionary.
    """
    config.update({
        'client_id': cfgget("devfid"),
        'server': server_ip,
        'port': server_port,
        'user': username,
        'password': password,
        'ssid': cfgget("staessid"),     # Only supports a single Wi-Fi connection. Multiple SSIDs not handled.
        'wifi_pw': cfgget("stapwd"),
        'keepalive': 120,
        'queue_len': 1,                 # Use event interface with default queue
        'will': (f'{cfgget("devfid")}/status', '{"status": "offline"}', True, 1)
    })
    return config


def load(username: str, password: str, server_ip: str, server_port: str='1883', qos: str=1):
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
    MQTT.CLIENT = MQTTClient(_configure(username, password, server_ip, server_port))
    MQTT.QOS = qos

    return micro_task(tag=MQTT.CLIENT_TASK, task=_init_client())


def help(widgets=False):
    """
    Show public functions. Return a tuple of public function usage strings for the MQTT module.
    :param widgets: Unused, reserved for extra help formatting.
    :return: Tuple of help strings.
    """
    return ('load username:str password:str server_ip:str server_port:str="1883"',
            'get_config',
            'publish topic:str message:str retain=False')

