from socket import getaddrinfo, SOCK_STREAM
from re import compile
import uasyncio as asyncio
from Debug import errlog_add
from Config import cfgget
from Server import Server
from Tasks import NativeTask


class InterCon:
    CONN_MAP = {}
    PORT = cfgget('socport')

    def __init__(self):
        self.reader = None
        self.writer = None
        self.auth_pwd = str.encode(cfgget('appwd'))        # Convert to bytes
        self.task = NativeTask()

    @staticmethod
    def validate_ipv4(str_in):
        pattern = compile(r'^(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])$')
        return bool(pattern.match(str_in))

    async def send_cmd(self, host, cmd):
        """
        Async Main method to implement device-device communication with
        - dhcp host resolve and IP caching
        - async connection with prompt check and command query and result handling (via Task cache/output)
        :param host: hostname or IP address to connect with
        :param cmd: command string to server socket shell
        """
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
                    Server.reply_all(f"[intercon] NoHost: {e}")
                    errlog_add(f"[intercon] send_cmd {host} oserr: {e}")
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
                Server.reply_all(f"[intercon] NoHost: {e}")
                errlog_add(f"[intercon] send_cmd {host} oserr: {e}")
                output = None
            finally:
                if self.writer:
                    self.writer.close()
                    await self.writer.wait_closed()

            # Cache successful connection data (hostname:IP)
            if hostname is not None:
                # In case of valid communication, store device IP; otherwise, set IP to None
                InterCon.CONN_MAP[hostname] = None if output is None else host
            # None: ServerBusy(or \0) or Prompt mismatch (auto delete cached IP), STR: valid comm. output
            return output
        else:
            errlog_add(f"[ERR][intercon] Invalid host: {host}")
        return ''

    async def __run_command(self, cmd, hostname):
        """
        Implements receive data on open connection, command query and result collection
        :param cmd: command string to server socket shell
        :param hostname: hostname for prompt checking
        Return None here will trigger retry mechanism... + deletes cached IP
        """
        cmd = str.encode(cmd)
        data, prompt = await self.__receive_data()
        if "Connection is busy. Bye!" in prompt:
            return None
        # Compare prompt |node01 $| with hostname 'node01.local'
        if hostname is None or prompt is None or str(prompt).replace('$', '').strip() == str(hostname).split('.')[0]:
            # Run command on validated device
            # TODO: Handle multiple cmd as input, separated by ; (????)
            self.writer.write(cmd)
            await self.writer.drain()
            data, _ = await self.__receive_data(prompt=prompt)
            if data == '\0':
                return None
            # Successful data receive, return data
            return data
        # Skip command run: prompt and host not the same!
        Server.reply_all(f"[intercon] prompt mismatch, hostname: {hostname} prompt: {prompt}")
        return None

    async def __auth_handshake(self, prompt):
        try:
            self.writer.write(self.auth_pwd)
            await self.writer.drain()
            data, prompt = await self.__receive_data(prompt=prompt)
        except Exception as e:
            errlog_add(f'[intercon][ERR] Auth: {e}')
            data = 'AuthFailed'
        if 'AuthOk' in data:
            return True             # AuthOk
        return False                # AuthFailed

    async def __receive_data(self, prompt=None):
        """
        Implements data receive loop until prompt / [configure] / Bye!
        :param prompt: socket shell prompt
        """
        data = ""
        # Collect answer data
        while True:
            try:
                last_data = await self.reader.read(128)
                if not last_data:
                    break
                last_data = last_data.decode('utf-8').strip()
                # First data is prompt, get it
                prompt = last_data.strip() if prompt is None else prompt
                data += last_data
                # Detect auth mode - pre-prompt: [password]
                if prompt.strip().startswith('[password]'):
                    prompt = prompt.replace('[password]', '').strip()
                    if not await self.__auth_handshake(prompt=prompt):
                        break       # AUTH FAILED
                # Wait for prompt or special cases (conf, exit)
                if prompt in data.strip() or '[configure]' in data or "Bye!" in last_data:
                    break
                #print(f"prompt: {prompt}, data: {data}")
            except OSError:
                break
        data = data.replace(prompt, '').replace('\n', ' ')
        return data, prompt


async def _send_cmd(host, cmd, com_obj):
    """
    Async send command wrapper for further async task integration and sync send_cmd usage (main)
    :param host: hostname / IP address
    :param cmd: command string to server socket shell
    :param com_obj: InterCon object to utilize send_cmd method and task status updates
    """
    # Send command
    with com_obj.task:
        for _ in range(0, 4):                           # Retry mechanism
            out = await com_obj.send_cmd(host, cmd)     # Send CMD
            if out is not None:                         # Retry mechanism
                break
            await asyncio.sleep_ms(100)                 # Retry mechanism
        com_obj.task.out = '' if out is None else out
    return com_obj.task.out


def send_cmd(host, cmd):
    """
    Sync wrapper of async _send_cmd (InterCon.send_cmd consumer with retry)
    :param host: hostname / IP address
    :param cmd: command string to server socket shell
    """
    def _tagify():
        nonlocal host, cmd
        _mod = cmd.split(' ')[0].strip()
        if InterCon.validate_ipv4(host):
            return f"{'.'.join(host.split('.')[-2:])}.{_mod}"
        return f"{host.replace('.local', '')}.{_mod}"

    com_obj = InterCon()
    tag = f"con.{_tagify()}"
    started = com_obj.task.create(callback=_send_cmd(host, cmd, com_obj), tag=tag)
    if started:
        result = {"verdict": f"Task started: task show {tag}", "tag": tag}
    else:
        result = {"verdict": "Task is Busy", "tag": tag}
    return result


def host_cache():
    """
    Dump InterCon connection cache
    """
    return InterCon.CONN_MAP

