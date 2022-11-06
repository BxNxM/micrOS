import socket
import select
import re
from Debug import errlog_add
from ConfigHandler import cfgget
from SocketServer import SocketServer


class InterCon:
    CONN_MAP = {}

    def __init__(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(2)         # become x2 due to retry

    @staticmethod
    def validate_ipv4(str_in):
        pattern = "^([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])$"
        if bool(re.match(pattern, str_in)):
            return True
        return False

    def send_cmd(self, host, port, cmd):
        hostname = None
        # Check IF host is hostname (example.local) and resolve it's IP address
        if not InterCon.validate_ipv4(host):
            hostname = host
            # Retrieve IP address by hostname dynamically
            if InterCon.CONN_MAP.get(hostname, None) is None:
                host = socket.getaddrinfo(host, port)[-1][4][0]
            else:
                # Restore IP from cache by hostname
                host = InterCon.CONN_MAP[hostname]
        # IF IP address is available send msg to the endpoint
        if InterCon.validate_ipv4(host):
            SocketServer().reply_message("[intercon] {} -> {}:{}:{}".format(cmd, hostname, host, port))

            # Send command over TCP/IP
            self.conn.connect((host, port))
            try:
                output = self.__run_command(cmd, hostname)
            except Exception as e:
                errlog_add("[intercon][ERR] send_cmd error: {}".format(e))
                output = None
            self.conn.close()

            # Cache successful connection data (hostname:IP)
            if hostname is not None:
                # In case of valid communication store device ip, otherwise set ip to None
                InterCon.CONN_MAP[hostname] = None if output is None else host
            return output
        else:
            errlog_add("[intercon][ERR] Invalid host: {}".format(host))
        return None

    def __run_command(self, cmd, hostname):
        cmd = str.encode(cmd)
        data, prompt = self.__receive_data()
        # Compare prompt |node01 $| with hostname 'node01.local'
        if hostname is None or prompt is None or str(prompt).replace('$', '').strip() == str(hostname).split('.')[0]:
            # Sun command on validated device
            self.conn.send(cmd)
            data, _ = self.__receive_data(prompt=prompt)
            if data == '\0':
                return None
            return data
        # Skip command run: prompt and host not the same!
        SocketServer().reply_message("[intercon] prompt mismatch, hostname: {} prompt: {} ".format(hostname, prompt))
        return None

    def __receive_data(self, prompt=None):
        data = ""
        # Collect answer data
        if select.select([self.conn], [], [], 1)[0]:
            while True:
                last_data = self.conn.recv(512).decode('utf-8').strip()
                # First data is prompt, get it
                prompt = last_data.strip() if prompt is None else prompt
                data += last_data
                # Wait for prompt or special cases (conf,exit)
                if prompt in data.strip() or '[configure]' in data or "Bye!" in last_data:
                    break
            data = data.replace(prompt, '')
            data = [k.strip() for k in data.split('\n')]
        return data, prompt


# Main command to send msg to other micrOS boards
def send_cmd(host, cmd):
    port = cfgget('socport')
    com_obj = InterCon()
    # send command
    output = com_obj.send_cmd(host, port, cmd)
    # send command retry
    if output is None:
        output = com_obj.send_cmd(host, port, cmd)
    return output


# Dump connection cache
def dump_cache():
    return InterCon.CONN_MAP
