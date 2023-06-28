import uasyncio as asyncio
from socket import getaddrinfo, AF_INET, SOCK_STREAM
from re import match
from Debug import errlog_add
from ConfigHandler import cfgget
from SocketServer import SocketServer
from TaskManager import Task


class InterCon:
    CONN_MAP = {}
    PORT = cfgget('socport')

    def __init__(self):
        self.reader = None
        self.writer = None
        self.task = Task()

    @staticmethod
    def validate_ipv4(str_in):
        pattern = r'^(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])$'
        if bool(match(pattern, str_in)):
            return True
        return False

    async def send_cmd(self, host, cmd):
        hostname = None
        # Check if host is a hostname (example.local) and resolve its IP address
        if not InterCon.validate_ipv4(host):
            hostname = host
            # Retrieve IP address by hostname dynamically
            if InterCon.CONN_MAP.get(hostname, None) is None:
                try:
                    addr_info = getaddrinfo(host, InterCon.PORT, 0, SOCK_STREAM)
                    host = addr_info[-1][4][0]
                except OSError as e:
                    SocketServer().reply_message("[intercon] NoHost: {}".format(e))
                    errlog_add("[intercon] send_cmd {} oserr: {}".format(host, e))
                    return ''
            else:
                # Restore IP from cache by hostname
                host = InterCon.CONN_MAP[hostname]
        # If IP address is available, send msg to the endpoint
        if InterCon.validate_ipv4(host):
            try:
                # Create socket object
                self.reader, self.writer = await asyncio.open_connection(host, InterCon.PORT)
                # Send command over TCP/IP
                output = await self.__run_command(cmd, hostname)
            except OSError as e:
                SocketServer().reply_message("[intercon] NoHost: {}".format(e))
                errlog_add("[intercon] send_cmd {} oserr: {}".format(host, e))
                output = None
            finally:
                if self.writer:
                    self.writer.close()
                    await self.writer.wait_closed()

            # Cache successful connection data (hostname:IP)
            if hostname is not None:
                # In case of valid communication, store device IP; otherwise, set IP to None
                InterCon.CONN_MAP[hostname] = None if output is None else host
            # Successful communication: list of received lines / Failed communication: None
            return '' if output is None else output
        else:
            errlog_add("[intercon][ERR] Invalid host: {}".format(host))
        return ''

    async def __run_command(self, cmd, hostname):
        cmd = str.encode(cmd)
        data, prompt = await self.__receive_data()
        if "Connection is busy. Bye!" in prompt:
            SocketServer().reply_message("Try later...")
            return None
        # Compare prompt |node01 $| with hostname 'node01.local'
        if hostname is None or prompt is None or str(prompt).replace('$', '').strip() == str(hostname).split('.')[0]:
            # Run command on validated device
            self.writer.write(cmd)
            await self.writer.drain()
            data, _ = await self.__receive_data(prompt=prompt)
            if data == '\0':
                return None
            # Successful data receive, return data
            return data
        # Skip command run: prompt and host not the same!
        SocketServer().reply_message("[intercon] prompt mismatch, hostname: {} prompt: {} ".format(hostname, prompt))
        return None

    async def __receive_data(self, prompt=None):
        data = ""
        # Collect answer data
        while True:
            try:
                last_data = await self.reader.read(256)
                if not last_data:
                    break
                last_data = last_data.decode('utf-8').strip()
                # First data is prompt, get it
                prompt = last_data.strip() if prompt is None else prompt
                data += last_data
                # Wait for prompt or special cases (conf, exit)
                if prompt in data.strip() or '[configure]' in data or "Bye!" in last_data:
                    break
            except OSError:
                break
        data = data.replace(prompt, '').replace('\n', ' ')
        return data, prompt


# Main command to send msg to other micrOS boards (async version)
async def _send_cmd(host, cmd, com_obj):
    # Send command
    with com_obj.task:
        com_obj.task.out = await com_obj.send_cmd(host, cmd)
    return output


# Main command to send msg to other micrOS boards (sync version)
def send_cmd(host, cmd):

    def _tagify():
        nonlocal host
        if InterCon.validate_ipv4(host):
            return '.'.join(host.split('.')[-2:])
        return host.replace('.local', '')

    com_obj = InterCon()
    tag = f"intercon.{_tagify()}"
    started = com_obj.task.create(callback=_send_cmd(host, cmd, com_obj), tag=tag)
    if started:
        result = {"verdict": f"Task started {host}:{cmd} -> task show {tag}", "tag": tag}
    else:
        result = {"verdict": "Task cannot start", "tag": tag}
    return result


# Dump connection cache
def dump_cache():
    return InterCon.CONN_MAP

