from socket import socket, getaddrinfo, AF_INET, SOCK_STREAM
from select import select
from re import match
from Debug import errlog_add
from ConfigHandler import cfgget
from SocketServer import SocketServer


class InterCon:
    CONN_MAP = {}
    PORT = cfgget('socport')

    def __init__(self, timeout):
        self.conn = socket(AF_INET, SOCK_STREAM)
        self.conn.settimeout(timeout)
        self.timeout = timeout

    @staticmethod
    def validate_ipv4(str_in):
        pattern = "^([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])$"
        if bool(match(pattern, str_in)):
            return True
        return False

    def send_cmd(self, host, cmd):
        hostname = None
        # Check IF host is hostname (example.local) and resolve it's IP address
        if not InterCon.validate_ipv4(host):
            hostname = host
            # Retrieve IP address by hostname dynamically
            if InterCon.CONN_MAP.get(hostname, None) is None:
                host = getaddrinfo(host, InterCon.PORT, 0, SOCK_STREAM)[-1][4][0]
            else:
                # Restore IP from cache by hostname
                host = InterCon.CONN_MAP[hostname]
        # IF IP address is available send msg to the endpoint
        if InterCon.validate_ipv4(host):
            SocketServer().reply_message("[intercon] {} -> {}:{}:{}".format(cmd, hostname, host, InterCon.PORT))

            try:
                # Connect to host
                self.conn.connect((host, InterCon.PORT))
                # Send command over TCP/IP
                output = self.__run_command(cmd, hostname)
            except OSError as e:
                SocketServer().reply_message("[intercon] NoHost: {}".format(e))
                errlog_add("[intercon] send_cmd {} oserr: {}".format(host, e))
                output = None
            try:
                self.conn.close()
            except:
                pass

            # Cache successful connection data (hostname:IP)
            if hostname is not None:
                # In case of valid communication store device ip, otherwise set ip to None
                InterCon.CONN_MAP[hostname] = None if output is None else host
            # Successful communication: list of received lines / Failed communication: None
            return [] if output is None else output
        else:
            errlog_add("[intercon][ERR] Invalid host: {}".format(host))
        return []

    def __run_command(self, cmd, hostname):
        cmd = str.encode(cmd)
        data, prompt = self.__receive_data()
        if "Connection is busy. Bye!" in prompt:
            SocketServer().reply_message("Try later...")
            return None
        # Compare prompt |node01 $| with hostname 'node01.local'
        if hostname is None or prompt is None or str(prompt).replace('$', '').strip() == str(hostname).split('.')[0]:
            # Sun command on validated device
            self.conn.send(cmd)
            data, _ = self.__receive_data(prompt=prompt)
            if data == '\0':
                return None
            # Successful data receive, return data
            return data
        # Skip command run: prompt and host not the same!
        SocketServer().reply_message("[intercon] prompt mismatch, hostname: {} prompt: {} ".format(hostname, prompt))
        return None

    def __receive_data(self, prompt=None):
        data = ""
        # Collect answer data
        if select([self.conn], [], [], self.timeout)[0]:
            while True:
                last_data = self.conn.recv(256).decode('utf-8').strip()
                # First data is prompt, get it
                prompt = last_data.strip() if prompt is None else prompt
                data += last_data
                # Wait for prompt or special cases (conf,exit)
                if prompt in data.strip() or '[configure]' in data or "Bye!" in last_data:
                    break
            data = data.replace(prompt, '')
            data = [k.strip() for k in data.strip().split('\n')]
        return data, prompt


# Main command to send msg to other micrOS boards
def send_cmd(host, cmd, timeout=1.0):
    com_obj = InterCon(timeout)
    # send command
    output = com_obj.send_cmd(host, cmd)
    return output


# Dump connection cache
def dump_cache():
    return InterCon.CONN_MAP
