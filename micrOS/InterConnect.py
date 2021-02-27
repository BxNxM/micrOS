import socket
import select
from time import sleep


def send_cmd(host, port, cmd):
    print("[INTERCON] {} -> {}:{}".format(cmd, host, port))
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((host, port))
    conn.settimeout(0.2)
    output = __run_command(conn, cmd)
    __close_connection(conn)
    return output


def __run_command(conn, cmd):
    cmd = str.encode(cmd)
    conn.send(cmd)
    data = __receive_data(conn)
    if data == '\0':
        print('intercon conn exiting...')
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
