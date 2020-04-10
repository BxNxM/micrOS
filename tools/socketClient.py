#!/usr/bin/env python3

import sys
import socket
import os
MYDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(MYDIR)
DEVENV_PATH = os.path.join(MYDIR, 'MicrOSDevEnv')
sys.path.append(DEVENV_PATH)
import select
import time
import nwscan
import json
from TerminalColors import Colors

#########################################################
#                 Device data handling                  #
#########################################################
class ConnectionData():
    HOST = 'localhost'
    PORT = 9008
    MICROS_DEV_IP_DICT = {}
    DEVICE_CACHE_PATH = os.path.join(MYDIR, "../user_data/device_conn_cache.json")
    DEFAULT_CONFIG_FRAGMNENT = { "__devuid__": [ \
                                                "192.168.4.1", \
                                                "__dev_mac_addr__", \
                                                "__default_device_on_AP__" \
                                                ],
                                  "__localhost__": [ \
                                                "127.0.0.1", \
                                                "__local_mac_addr__", \
                                                "device_localhost"
                                               ] }

    @staticmethod
    def filter_MicrOS_devices():
        filtered_devices = nwscan.filter_by_open_port(device_ip_list=nwscan.map_wlan_devices(), port=ConnectionData.PORT)
        for device in filtered_devices:
            socket = None
            if '.' in device[0]:
                try:
                    if not (device[0].startswith('10.') or device[0].startswith('192.')):
                        print("Invalid device IP:{} - skip".format(device[0]))
                        continue
                    print("Device Query on {} ...".format(device[0]))
                    socket = SocketDictClient(host=device[0], port=ConnectionData.PORT)
                    reply = socket.non_interactive('hello')
                    if "hello" in reply:
                        print("[MicrOS] Device: {} reply: {}".format(device[0], reply))
                        fuid = reply.split(':')[1]
                        uid = reply.split(':')[2]
                        ConnectionData.MICROS_DEV_IP_DICT[uid] = [device[0], device[1], fuid]
                    else:
                        print("[Non MicrOS] Device: {} reply: {}".format(device[0], reply))
                except Exception as e:
                    print("{} scan warning: {}".format(device, e))
                finally:
                    if socket is not None and socket.conn is not None:
                        socket.conn.close()
                    del socket
        ConnectionData.write_MicrOS_device_cache(ConnectionData.MICROS_DEV_IP_DICT)
        print("AVAILABLE MICROS DEVICES:\n{}".format(json.dumps(ConnectionData.MICROS_DEV_IP_DICT, indent=4, sort_keys=True)))

    @staticmethod
    def write_MicrOS_device_cache(device_dict):
        ConnectionData.read_MicrOS_device_cache()
        cache_path = ConnectionData.DEVICE_CACHE_PATH
        print("Write MicrOS device cache: {}".format(cache_path))
        with open(cache_path, 'w') as f:
            ConnectionData.MICROS_DEV_IP_DICT.update(ConnectionData.DEFAULT_CONFIG_FRAGMNENT)
            ConnectionData.MICROS_DEV_IP_DICT.update(device_dict)
            json.dump(ConnectionData.MICROS_DEV_IP_DICT, f, indent=4)

    @staticmethod
    def read_MicrOS_device_cache():
        cache_path = ConnectionData.DEVICE_CACHE_PATH
        if os.path.isfile(cache_path):
            print("Load MicrOS device cache: {}".format(cache_path))
            with open(cache_path, 'r') as f:
                cache_content = json.load(f)
                cache_content.update(ConnectionData.MICROS_DEV_IP_DICT)
                ConnectionData.MICROS_DEV_IP_DICT = cache_content
        else:
            print("Load MicrOS device cache not found: {}".format(cache_path))
        return ConnectionData.MICROS_DEV_IP_DICT

    @staticmethod
    def select_device(dev=None):
        device_choose_list = []
        device_was_found = False
        if dev is None:
            print("Activate MicrOS device connection address")
        if len(list(ConnectionData.MICROS_DEV_IP_DICT.keys())) == 1:
            key = list(ConnectionData.MICROS_DEV_IP_DICT.keys())[0]
            ConnectionData.HOST = ConnectionData.MICROS_DEV_IP_DICT[key][0]
        else:
            if dev is None:
                print("{}[i]         FUID        IP               UID{}".format(Colors.OKGREEN, Colors.NC))
            for index, device in enumerate(ConnectionData.MICROS_DEV_IP_DICT.keys()):
                uid = device
                devip = ConnectionData.MICROS_DEV_IP_DICT[device][0]
                fuid = ConnectionData.MICROS_DEV_IP_DICT[device][2]
                if dev is None:
                    print("[{}{}{}] Device: {}{}{} - {} - {}".format(Colors.BOLD, index, Colors.NC, \
                                                                 Colors.OKBLUE, fuid, Colors.NC, \
                                                                 devip, uid))
                device_choose_list.append(devip)
                if device is not None:
                    if dev == uid or dev == devip or dev == fuid:
                        print("{}Device was found: {}{}".format(Colors.OK, dev, Colors.NC))
                        ConnectionData.HOST = devip
                        device_was_found = True
                        break
            if not device_was_found:
                if len(device_choose_list) > 1:
                    index = int(input("{}Choose a device index: {}".format(Colors.OK, Colors.NC)))
                    ConnectionData.HOST = device_choose_list[index]
                    print("Device IP was set: {}".format(ConnectionData.HOST))
                else:
                    print("{}Device not found.{}".format(Colors.ERR, Colors.NC))
                    sys.exit(0)

    @staticmethod
    def auto_execute(search=False, status=False, dev=None):
        if not os.path.isfile(ConnectionData.DEVICE_CACHE_PATH):
            search = True
        if search:
            ConnectionData.filter_MicrOS_devices()
        else:
            ConnectionData.read_MicrOS_device_cache()
        if status:
            ConnectionData.nodes_status()
            sys.exit(0)
        ConnectionData.select_device(dev=dev)
        ConnectionData.read_port_from_nodeconf()
        return ConnectionData.HOST, ConnectionData.PORT

    @staticmethod
    def read_port_from_nodeconf():
        base_path = MYDIR + os.sep + ".." + os.sep + "MicrOS" + os.sep
        config_path = base_path + "node_config.json"
        confighandler_path = base_path + "ConfigHandler.py"
        port_data = ""
        if os.path.isfile(config_path):
            with open(config_path) as json_file:
                port_data = json.load(json_file)['socport']
            try:
                ConnectionData.PORT = int(port_data)
            except:
                print("PORT: {} from {} invalid, must be integer".format(port_data, config_path))
        else:
            print("PORT INFORMATION COMES FROM: {}, but not exists!\n\t[HINT] Run {} script to generate default MicrOS config.".format(config_path, confighandler_path))

    @staticmethod
    def nodes_status():
        spr_offset1 = 30
        nodes_dict = ConnectionData.read_MicrOS_device_cache()
        spacer1 = " " * (spr_offset1-14)
        print("{cols}       [ UID ]{spr1}[ FUID ]\t[ IP ]\t\t[ STATUS ]\t[ MEMFREE ]\t[ VERSION ]{cole}"\
              .format(spr1=spacer1, cols=Colors.OKBLUE+Colors.BOLD, cole=Colors.NC))
        for uid, data in nodes_dict.items():
            ip = data[0]
            fuid = "{}{}{}".format(Colors.HEADER, data[2], Colors.NC)
            if uid not in ['__devuid__', '__localhost__']:
                spacer1 = " "*(spr_offset1 - len(uid))

                # print status msgs
                is_online = "{}ONLINE{}".format(Colors.OK, Colors.NC) if nwscan.node_is_online(ip, port=ConnectionData.PORT) else "{}OFFLINE{}".format(Colors.WARN, Colors.NC)
                mem_data = '<memfree>'
                version_data = '<n/a>'

                # is online
                if 'ONLINE' in is_online:
                    # get mem_data
                    mem_data = SocketDictClient(\
                        host=ip, port=ConnectionData.PORT, silent_mode=True).non_interactive(['system memfree'])
                    mem_data = "{} byte".format(str(mem_data.split('\n')[1]).split(':')[-1])
                    # get version data
                    version_data = SocketDictClient( \
                        host=ip, port=ConnectionData.PORT, silent_mode=True).non_interactive(['version'])

                # Generate line printout
                data_line_str = "{uid}{spr1}{fuid}\t{ip}\t{stat}\t\t{mem}\t{version}" \
                    .format(uid=uid, spr1=spacer1, fuid=fuid, ip=ip,\
                            stat=is_online, mem=mem_data, version=version_data)
                # Print line
                print(data_line_str)

#########################################################
#               Socket Client Class                     #
#########################################################


class SocketDictClient():

    def __init__(self, host='localhost', port=9008, bufsize=4096, silent_mode=False):
        self.silent_mode = silent_mode
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

    def receive_data(self, wait_before_msg=1):
        data = ""
        data_list = []
        if select.select([self.conn], [], [], 3)[0]:
            if self.is_interactive:
                time.sleep(wait_before_msg)
                data = self.conn.recv(self.bufsize).decode('utf-8')
                data_list = data.split('\n')
            else:
                while data == "":
                    time.sleep(wait_before_msg)
                    data += self.conn.recv(self.bufsize).decode('utf-8')
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
        ret_msg = self.command_pipeline(cmd_args)
        return ret_msg

    def command_pipeline(self, cmd_args, separator='<a>'):
        cmd_pipeline = cmd_args.split(separator)
        ret_msg = ""
        for cmd in cmd_pipeline:
            cmd = cmd.strip()
            ret_msg = self.console(self.run_command(cmd))
        self.close_connection()
        return ret_msg

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
        if not self.silent_mode:
            print(str_msg, end=end)
        return str_msg

#########################################################
#                       MAIN                            #
#########################################################


def socket_commandline_args(arg_list):
    return_action_dict = {'search': False, 'dev': None, 'status': False}
    if "--scan" in arg_list:
        arg_list.remove("--scan")
        return_action_dict['search'] = True
    if "--stat" in arg_list:
        arg_list.remove("--stat")
        return_action_dict['status'] = True
    if "--dev" in arg_list:
        for index, arg in enumerate(arg_list):
            if arg == "--dev":
                return_action_dict['dev'] = arg_list[index+1]
                arg_list.remove("--dev")
                arg_list.remove(return_action_dict['dev'])
                break
    if "--help" in arg_list:
        print("--scan\t\t- scan devices")
        print("--dev\t\t- select device - value should be: fuid or uid or devip")
        print("--stat\t\t- show devides online/offline - and memory data")
        print("HINT\t\t- In non interactive mode you can pipe commands with <a> separator")
        sys.exit(0)
    return arg_list, return_action_dict


def main(args):
    try:
        socketdictclient = SocketDictClient(host=ConnectionData.HOST, port=ConnectionData.PORT)
        if len(args) == 0:
            socketdictclient.interactive()
        else:
            socketdictclient.non_interactive(args)
        return True
    except KeyboardInterrupt:
        return True
    except Exception as e:
        if "Connection reset by peer" not in str(e):
            print("FAILED TO START: " + str(e))
        return False


def run(arg_list=[]):
    args, action = socket_commandline_args(arg_list)
    ConnectionData.auto_execute(search=action['search'], status=action['status'],  dev=action['dev'])
    return main(args)


if __name__ == "__main__":
    args, action = socket_commandline_args(sys.argv[1:])
    ConnectionData.auto_execute(search=action['search'], status=action['status'], dev=action['dev'])
    main(args)
