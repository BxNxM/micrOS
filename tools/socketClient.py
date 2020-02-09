#!/usr/bin/env python3

import sys
import socket
import os
myfolder = os.path.dirname(os.path.abspath(__file__))
sys.path.append(myfolder)
import select
import time

class ConnectionData():
    HOST = 'localhost'
    PORT = 9008

class SocketDictClient():

    def __init__(self, host='localhost', port=9008, bufsize=4096):
        self.is_interactive = False
        self.bufsize = bufsize
        self.host = host
        self.port = port
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((host, port))

    def run_command(self, cmd, info=False):
        cmd = str.encode(cmd)
        self.conn.send(cmd)
        data = self.receive_data()
        if info:
            msglen = len(data)
            self.console("got: {}".format(data))
            self.console("received: {}".format(msglen))
        if data == '\0':
            self.console('exiting...')
            self.close_connection()
            sys.exit(0)
        return data

    def receive_data(self):
        data = ""
        data_list = []
        if select.select([self.conn], [], [], 0.2)[0]:
            time.sleep(1)
            data = self.conn.recv(self.bufsize).decode('utf-8')
            data_list = data.split('\n')
        return data, data_list

    def interactive(self):
        self.is_interactive = True
        self.console(self.receive_data(), end='')
        while True:
            cmd = input()
            if cmd != "":
                self.console(self.run_command(cmd), end='')
                if cmd.rstrip() == "exit":
                    self.close_connection()
                    sys.exit(0)

    def non_interactive(self, cmd_list):
        self.is_interactive = False
        if isinstance(cmd_list, list):
            cmd_args = " ".join(cmd_list).strip()
        elif isinstance(cmd_list, str):
            cmd_args = cmd_list
        else:
            Exception("non_interactive function input must be list ot str!")
        self.console(socketdictclient.run_command(cmd_args))
        self.close_connection()

    def close_connection(self):
        self.run_command("exit")
        self.conn.close()

    def console(self, msg, end='\n', server_pronpt_sep=' $'):
        if isinstance(msg, list) or isinstance(msg, tuple):
            str_msg = str(msg[0])
            list_msg = msg[1]
            if not self.is_interactive:
                input_list_buff = [k.split(server_pronpt_sep) for k in list_msg]
                filtered_msg = ""
                for line in input_list_buff:
                    if len(line) > 1:
                        for word in line[1:]:
                            filtered_msg += word + "\n"
                    else:
                        filtered_msg += ''.join(line) + "\n"
                str_msg = filtered_msg.strip()
        else:
            str_msg = msg
        print(str_msg, end=end)

if __name__ == "__main__":
    try:
        socketdictclient = SocketDictClient(host=ConnectionData.HOST, port=ConnectionData.PORT)
        if len(sys.argv[1:]) == 0:
            socketdictclient.interactive()
        else:
            socketdictclient.non_interactive(sys.argv[1:])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        if "Connection reset by peer" not in str(e):
            print("FAILED TO START: " + str(e))
