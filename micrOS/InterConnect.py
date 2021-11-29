import socket
import select
import re
from time import sleep
from Debug import errlog_add
from ConfigHandler import cfgget
from SocketServer import SocketServer


def validate_ipv4(str_in):
    pattern = "^([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])$"
    if bool(re.match(pattern, str_in)):
        return True
    return False


def send_cmd(host, cmd):
    port = cfgget('socport')
    hostname = None
    if not validate_ipv4(host):
        hostname = host
        host = socket.getaddrinfo(host, port)[-1][4][0]
    if validate_ipv4(host):
        # Socket reply msg
        SocketServer().reply_message("[intercon] {} -> {}:{}:{}".format(cmd, hostname, host, port))
        # Send CMD
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(5)
        conn.connect((host, port))
        output = __run_command(conn, cmd)
        __close_connection(conn)
        return output
    else:
        errlog_add("[INTERCON] Invalid host: {}".format(host))
        return None


def __run_command(conn, cmd):
    cmd = str.encode(cmd)
    conn.send(cmd)
    data = __receive_data(conn)
    if data == '\0':
        # print('[INTERCON] exiting...')
        __close_connection(conn)
        return None
    return data


def __close_connection(conn):
    __run_command(conn, "exit")
    conn.close()


def __receive_data(conn, wait_before_msg=0.2):
    data = ""
    prompt_postfix = ' $'
    data_list = []
    if select.select([conn], [], [], 1)[0]:
        while True:
            sleep(wait_before_msg)
            last_data = conn.recv(512).decode('utf-8')
            data += last_data
            # Msg reply wait criteria (get the prompt back or special cases)
            if len(data.split('\n')) > 1 or '[configure]' in data:
                # wait for all msg in non-interactive mode until expected msg or prompt return
                if prompt_postfix in data.split('\n')[-1] or "Bye!" in last_data:
                    break
        # Split raw data list
        full_prompt = "{}{}".format(data.split(prompt_postfix.strip())[0].strip(), prompt_postfix)
        data = data.replace(full_prompt, '').strip()
        data_list = data.split('\n')
    return data_list
