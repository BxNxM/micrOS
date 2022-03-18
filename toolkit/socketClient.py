#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import socket
import os
import select
import time
import json
import threading

MYDIR = os.path.dirname(__file__)
print("Module [socketClient] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYDIR))
try:
    from .lib import SearchDevices
    from .lib.TerminalColors import Colors
    from .lib.LocalMachine import FileHandler
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    import lib.SearchDevices as SearchDevices
    from lib.TerminalColors import Colors
    from lib.LocalMachine import FileHandler


#########################################################
#                 Device data handling                  #
#########################################################


class ConnectionData:
    # UID: [IP, PORT, FUID]
    MICROS_DEVICES = {}
    DEVICE_CACHE_PATH = os.path.join(MYDIR, "user_data/device_conn_cache.json")
    DEFAULT_CONFIG_FRAGMNENT = {"__devuid__": [
        "192.168.4.1",
        9008,
        "__device_on_AP__"
    ],
        "__localhost__": [
            "127.0.0.1",
            9008,
            "__simulator__"
        ]}

    @staticmethod
    def auto_execute(search=False, status=False, dev=None):
        if not os.path.isfile(ConnectionData.DEVICE_CACHE_PATH):
            search = True
        if search:
            ConnectionData.search_micrOS_on_wlan()
        else:
            ConnectionData.read_micrOS_device_cache()
        if status:
            ConnectionData.nodes_status()
            sys.exit(0)
        # IP, PORT, FID, UID
        return ConnectionData.select_device(device_tag=dev)

    @staticmethod
    def __handshake_with_device_on_ip(ip, port, thread_name):
        """
        :param device: device data
        :param thread_name: thread identifier (index)
        Update ConnectionData.MICROS_DEVICES with new devices
        """
        socket_obj = None
        if '.' in ip:
            try:
                if not (ip.startswith('10.') or ip.startswith('192.')):
                    print("[{}]Invalid device IP:{} - skip".format(thread_name, ip[0]))
                    return
                print("Device Query on {}:{}".format(ip, port))
                socket_obj = SocketDictClient(host=ip, port=port)
                reply = socket_obj.non_interactive('hello')
                if "hello" in reply:
                    fuid = reply.split(':')[1]
                    uid = reply.split(':')[2]
                    # !!! Add device to known list: UID: [IP, PORT, FID, MAC]
                    ConnectionData.MICROS_DEVICES[uid] = [ip, port, fuid]
                    print("[{}][micrOS] Device: {} - {}:{} reply: {}".format(thread_name, fuid, ip, port, reply))
                else:
                    print("[{}][Non micrOS] Device: {} reply: {}".format(thread_name, ip, reply))
            except Exception as e:
                print("[{}] {} scan warning: {}:{}".format(thread_name, ip, port, e))
            finally:
                if socket_obj is not None and socket_obj.conn is not None:
                    socket_obj.conn.close()
                del socket_obj

    @staticmethod
    def search_micrOS_on_wlan(service_port=9008):
        start_time = time.time()
        # start wlan search on entire ip range on a given port
        filtered_ip_list = SearchDevices.online_device_scanner(service_port=service_port)
        # initiate search threads with micrOS handshake callback
        thread_instance_list = []
        for index, device_ip in enumerate(filtered_ip_list):
            thread_name = "thread-{} check: {}".format(index, device_ip)
            thread_instance_list.append(
                threading.Thread(target=ConnectionData.__handshake_with_device_on_ip, args=(device_ip, service_port, thread_name,))
            )

        # Start threads
        for mythread in thread_instance_list:
            mythread.start()

        # Wait for threads
        for mythread in thread_instance_list:
            mythread.join()

        end_time = time.time()
        # Dump the result
        print("SEARCH TOTAL ELAPSED TIME: {} sec".format(end_time - start_time))
        # Save result to micrOS config cache + file
        ConnectionData.save_micrOS_device_cache()
        print(
            "AVAILABLE MICROS DEVICES:\n{}".format(json.dumps(ConnectionData.MICROS_DEVICES, indent=4, sort_keys=True)))

    @staticmethod
    def save_micrOS_device_cache():
        ConnectionData.read_micrOS_device_cache()
        cache_path = ConnectionData.DEVICE_CACHE_PATH
        print("Write micrOS device cache: {}".format(cache_path))
        with open(cache_path, 'w') as f:
            ConnectionData.DEFAULT_CONFIG_FRAGMNENT.update(ConnectionData.MICROS_DEVICES)
            json.dump(ConnectionData.MICROS_DEVICES, f, indent=4)

    @staticmethod
    def read_micrOS_device_cache():
        cache_path = ConnectionData.DEVICE_CACHE_PATH
        if os.path.isfile(cache_path):
            print("Load micrOS device cache: {}".format(cache_path))
            with open(cache_path, 'r') as f:
                cache_content = json.load(f)
                cache_content.update(ConnectionData.MICROS_DEVICES)
                ConnectionData.MICROS_DEVICES = cache_content
        else:
            print("Load micrOS device cache not found: {}".format(cache_path))
            ConnectionData.MICROS_DEVICES = ConnectionData.DEFAULT_CONFIG_FRAGMNENT
        return ConnectionData.MICROS_DEVICES

    @staticmethod
    def select_device(device_tag=None):
        """
        :param device_tag: uid or devip or fuid
        :return: IP, PORT, FID
        """
        # Select by device_tag param
        if len(ConnectionData.MICROS_DEVICES) == 0:
            print("Retrieve MICROS_DEVICES")
            ConnectionData.read_micrOS_device_cache()
        for index, uid in enumerate(ConnectionData.MICROS_DEVICES.keys()):
            if uid is not None:
                device = ConnectionData.MICROS_DEVICES[uid]
                # Match with IP, FID, UID
                if device_tag == device[0] or device_tag == device[2] or device_tag == uid:
                    print("{}Device was found: {}{}".format(Colors.OK, device_tag, Colors.NC))
                    # IP, PORT, FID, UID
                    return device[0], device[1], device[2], uid

        # Manual select
        uid_list_to_select = []
        print("{}[i]         FUID        IP               UID{}".format(Colors.OKGREEN, Colors.NC))
        for index, uid in enumerate(ConnectionData.MICROS_DEVICES.keys()):
            devip = ConnectionData.MICROS_DEVICES[uid][0]
            fuid = ConnectionData.MICROS_DEVICES[uid][2]
            print("[{}{}{}] Device: {}{}{} - {} - {}".format(Colors.BOLD, index, Colors.NC,
                                                             Colors.OKBLUE, fuid, Colors.NC,
                                                             devip, uid))
            uid_list_to_select.append(uid)
        if len(uid_list_to_select) > 1:
            index = int(input("{}Choose a device index: {}".format(Colors.OK, Colors.NC)))
            device = ConnectionData.MICROS_DEVICES[uid_list_to_select[index]]
            print("Device was selected: {}".format(device))
            # IP, PORT, FID, UID
            return device[0], device[1], device[2], uid_list_to_select[index]
        else:
            print("{}Device not found.{}".format(Colors.ERR, Colors.NC))
            sys.exit(0)

    @staticmethod
    def nodes_status():
        spr_offset1 = 30
        spr_offset2 = 57
        nodes_dict = ConnectionData.read_micrOS_device_cache()
        spacer1 = " " * (spr_offset1 - 14)
        print("{cols}       [ UID ]{spr1}[ FUID ]\t\t[ IP ]\t\t[ STATUS ]\t[ VERSION ]\t[COMM SEC]{cole}"
              .format(spr1=spacer1, cols=Colors.OKBLUE + Colors.BOLD, cole=Colors.NC))
        for uid, data in nodes_dict.items():
            ip = data[0]
            port = data[1]
            fuid = "{}{}{}".format(Colors.HEADER, data[2], Colors.NC)
            if uid not in ['__devuid__']:
                spacer1 = " " * (spr_offset1 - len(uid))

                # print status msgs
                is_online = "{}ONLINE{}".format(Colors.OK, Colors.NC) if SearchDevices.node_is_online(ip, port=port) else "{}OFFLINE{}".format(
                    Colors.WARN, Colors.NC)
                version_data = '<n/a>'
                elapsed_time = 'n/a'

                # is online
                if 'ONLINE' in is_online:
                    # get version data
                    try:
                        start_comm = time.time()
                        version_data = SocketDictClient(host=ip, port=port, silent_mode=True).non_interactive(['version'])
                        elapsed_time = "{:.3f}".format(time.time() - start_comm)
                    except:
                        pass

                # Generate line printout
                base_info = "{uid}{spr1}{fuid}".format(uid=uid, spr1=spacer1, fuid=fuid)
                spacer1 = " " * (spr_offset2 - len(base_info))
                data_line_str = "{base}{spr2}{ip}\t{stat}\t\t{version}\t\t{elapt}" \
                    .format(base=base_info, spr2=spacer1, ip=ip,
                            stat=is_online, version=version_data, elapt=elapsed_time)
                # Print line
                print(data_line_str)

    @staticmethod
    def clean_cache():
        print("Remove user cache: {}".format(ConnectionData.DEVICE_CACHE_PATH))
        FileHandler.remove(ConnectionData.DEVICE_CACHE_PATH)

    @staticmethod
    def list_devices():
        print("micrOS devices:")
        device_struct = ConnectionData.read_micrOS_device_cache()
        for k in device_struct.keys():
            print("{}: {}".format(k, device_struct[k]))
        return device_struct

    @staticmethod
    def resolve_hostname(fuid, uid):
        local_dhcp_hostname = "{}.local".format(fuid.strip())
        try:
            ip = socket.gethostbyname(local_dhcp_hostname)
            data = ConnectionData.MICROS_DEVICES[uid]
            if '.' in ip and data[0] != ip:
                data[0] = ip
                ConnectionData.MICROS_DEVICES[uid] = data
                ConnectionData.save_micrOS_device_cache()
            # host, port, fid, uid
            return data[0], data[1], data[2], uid
        except Exception as e:
            print("Cannot resolve hostname: {}: {}".format(local_dhcp_hostname, e))
        return None, None, None, None


#########################################################
#               Socket Client Class                     #
#########################################################


class SocketDictClient:

    def __init__(self, host='localhost', port=9008, bufsize=4096, silent_mode=False, tout=6):
        self.silent_mode = silent_mode
        self.is_interactive = False
        self.bufsize = bufsize
        self.host = host
        self.port = port
        self.tout = tout
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(self.tout)
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
        prompt_postfix = ' $'
        data_list = []
        if select.select([self.conn], [], [], 3)[0]:
            while True:
                time.sleep(0.2)
                last_data = self.conn.recv(self.bufsize).decode('utf-8')
                data += last_data
                # Msg reply wait criteria (get the prompt back or special cases)
                if not self.is_interactive and (len(data.split('\n')) > 1 or '[configure]' in data):
                    # wait for all msg in non-interactive mode until expected msg or prompt return
                    if prompt_postfix in data.split('\n')[-1] or "Bye!" in last_data:
                        break
                elif self.is_interactive and (prompt_postfix in data.split('\n')[-1] or "Bye!" in last_data):
                    # handle interactive mode: return msg when the prompt or expected output returns
                    break
            # Split raw data list
            data_list = data.split('\n')
        return data, data_list

    def interactive(self):
        self.is_interactive = True
        self.console(self.receive_data(), end='')
        while True:
            cmd = input().strip()
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
            try:
                print(str_msg, end=end)
            except UnicodeEncodeError:
                print(str_msg.encode('ascii', 'ignore').decode('ascii'), end=end)
        return str_msg


#########################################################
#                       MAIN                            #
#########################################################


def main(args, host='127.0.0.1', port=9008, timeout=3):
    """ main connection wrapper function """
    answer_msg = None
    socketdictclient = None
    try:
        socketdictclient = SocketDictClient(host=host, port=port, tout=timeout)
        if len(args) == 0:
            # INTERACTIVE MODE
            socketdictclient.interactive()
        else:
            # NON INTERACTIVE MODE WITH ARGS
            answer_msg = socketdictclient.non_interactive(args)
        return True, answer_msg
    except KeyboardInterrupt:
        try:
            if socketdictclient is not None:
                socketdictclient.close_connection()
        except Exception as e:
            print(e)
            pass
        sys.exit(0)
    except Exception as e:
        print("Socket communication error: {}".format(e))
        if "timed out" in str(e) or "Host is down" in str(e):
            raise Exception("TimeOut")
    return False, answer_msg


def socket_commandline_args(arg_list):
    if arg_list is None or len(arg_list) == 0:
        arg_list = sys.argv[1:]
    return_action_dict = {'search': False, 'device_tag': None, 'status': False}
    if len(arg_list) > 0 and 'scan' in arg_list[0]:
        del arg_list[0]
        return_action_dict['search'] = True
    if len(arg_list) > 0 and 'stat' in str(arg_list[0]):
        del arg_list[0]
        return_action_dict['status'] = True
    if len(arg_list) > 0 and "dev" in arg_list[0]:
        return_action_dict['device_tag'] = arg_list[1]
        del arg_list[0:2]
    if len(arg_list) > 0 and 'clean' in arg_list[0]:
        ConnectionData.clean_cache()
        sys.exit()
    if len(arg_list) > 0 and 'list' in arg_list[0]:
        ConnectionData.list_devices()
        sys.exit()
    if len(arg_list) > 0 and ("man" in arg_list[0] or "hint" in arg_list[0]):
        print("--scan / scan\t\t- scan devices")
        print("--dev / dev\t\t- select device - value should be: fuid or uid or devip")
        print("--stat / stat\t\t- show devides online/offline - and memory data")
        print("--clean / clean\t\t- clean device_conn_cache.json")
        print("--list / list\t\t- list mocrOS devices")
        print("HINT\t\t- In non interactive mode you can pipe commands with <a> separator")
        sys.exit(0)
    return arg_list, return_action_dict


def run(arg_list=[]):
    """ Run from code
        - Handles extra command line arguments
    """
    print("Socket run (raw): {}".format(arg_list))
    args, action = socket_commandline_args(arg_list)
    host, port, fid, uid = ConnectionData.auto_execute(search=action['search'], status=action['status'], dev=action['device_tag'])
    output = False, ''
    try:
        output = main(args, host=host, port=port)
    except Exception as e:
        if "TimeOut" in str(e):
            print("Resolve device by host ... {}.local {}:{}:{}".format(fid, host, port, uid))
            # host, port, fid, uid
            ConnectionData.resolve_hostname(fid, uid)
    return output


if __name__ == "__main__":
    """Runs in individual - direct execution mode"""
    run()
