#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
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
    from .lib import nwscan
    from .lib.TerminalColors import Colors
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    import lib.nwscan as nwscan
    from lib.TerminalColors import Colors

#########################################################
#                 Device data handling                  #
#########################################################


class ConnectionData:
    HOST = 'localhost'
    PORT = 9008
    MICROS_DEV_IP_DICT = {}
    DEVICE_CACHE_PATH = os.path.join(MYDIR, "user_data/device_conn_cache.json")
    DEFAULT_CONFIG_FRAGMNENT = { "__devuid__": [
                                                "192.168.4.1",
                                                "__dev_mac_addr__",
                                                "__device_on_AP__"
                                                ],
                                  "__localhost__": [
                                                "127.0.0.1",
                                                "__local_mac_addr__",
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
        ConnectionData.select_device(device_tag=dev)
        return ConnectionData.HOST, ConnectionData.PORT

    @staticmethod
    def __handshake_with_device_on_ip(device, thread_name):
        """
        :param device: device data
        :param thread_name: thread identifier (index)
        Update ConnectionData.MICROS_DEV_IP_DICT with new devices
        """
        socket_obj = None
        if '.' in device[0]:
            try:
                if not (device[0].startswith('10.') or device[0].startswith('192.')):
                    print("[{}]Invalid device IP:{} - skip".format(thread_name, device[0]))
                    return
                print("Device Query on {} ...".format(device[0]))
                socket_obj = SocketDictClient(host=device[0], port=ConnectionData.PORT)
                reply = socket_obj.non_interactive('hello')
                if "hello" in reply:
                    print("[{}][micrOS] Device: {} reply: {}".format(thread_name, device[0], reply))
                    fuid = reply.split(':')[1]
                    uid = reply.split(':')[2]
                    # Add device to known list
                    ConnectionData.MICROS_DEV_IP_DICT[uid] = [device[0], device[1], fuid]
                else:
                    print("[{}][Non micrOS] Device: {} reply: {}".format(thread_name, device[0], reply))
            except Exception as e:
                print("[{}] {} scan warning: {}".format(thread_name, device, e))
            finally:
                if socket_obj is not None and socket_obj.conn is not None:
                    socket_obj.conn.close()
                del socket_obj

    @staticmethod
    def search_micrOS_on_wlan():
        start_time = time.time()
        # start wlan search on entire ip range on a given port
        filtered_devices = nwscan.map_wlan_devices(service_port=9008)
        # initiate search threads with micrOS handshake callback
        thread_instance_list = []
        for index, device in enumerate(filtered_devices):
            thread_name = "thread-{} check: {}".format(index, device)
            thread_instance_list.append(
                threading.Thread(target=ConnectionData.__handshake_with_device_on_ip, args=(device, thread_name,))
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
        ConnectionData.save_micrOS_device_cache(ConnectionData.MICROS_DEV_IP_DICT)
        print("AVAILABLE MICROS DEVICES:\n{}".format(json.dumps(ConnectionData.MICROS_DEV_IP_DICT, indent=4, sort_keys=True)))

    @staticmethod
    def save_micrOS_device_cache(device_dict):
        ConnectionData.read_micrOS_device_cache()
        cache_path = ConnectionData.DEVICE_CACHE_PATH
        print("Write micrOS device cache: {}".format(cache_path))
        with open(cache_path, 'w') as f:
            ConnectionData.MICROS_DEV_IP_DICT.update(ConnectionData.DEFAULT_CONFIG_FRAGMNENT)
            ConnectionData.MICROS_DEV_IP_DICT.update(device_dict)
            json.dump(ConnectionData.MICROS_DEV_IP_DICT, f, indent=4)

    @staticmethod
    def read_micrOS_device_cache():
        cache_path = ConnectionData.DEVICE_CACHE_PATH
        if os.path.isfile(cache_path):
            print("Load micrOS device cache: {}".format(cache_path))
            with open(cache_path, 'r') as f:
                cache_content = json.load(f)
                cache_content.update(ConnectionData.MICROS_DEV_IP_DICT)
                ConnectionData.MICROS_DEV_IP_DICT = cache_content
        else:
            print("Load micrOS device cache not found: {}".format(cache_path))
            ConnectionData.MICROS_DEV_IP_DICT = ConnectionData.DEFAULT_CONFIG_FRAGMNENT
        return ConnectionData.MICROS_DEV_IP_DICT

    @staticmethod
    def select_device(device_tag=None):
        """
        :param device_tag: uid or devip or fuid
        :return: ConnectionData.HOST, device_fid
        """
        device_choose_list = []
        device_fid_in_order = []
        device_was_found = False
        device_fid = None
        if len(ConnectionData.MICROS_DEV_IP_DICT) == 0:
            print("Retrieve MICROS_DEV_IP_DICT")
            ConnectionData.read_micrOS_device_cache()
        if len(list(ConnectionData.MICROS_DEV_IP_DICT.keys())) == 1:
            key = list(ConnectionData.MICROS_DEV_IP_DICT.keys())[0]
            ConnectionData.HOST = ConnectionData.MICROS_DEV_IP_DICT[key][0]
        else:
            for index, device in enumerate(ConnectionData.MICROS_DEV_IP_DICT.keys()):
                uid = device
                devip = ConnectionData.MICROS_DEV_IP_DICT[device][0]
                fuid = ConnectionData.MICROS_DEV_IP_DICT[device][2]
                if device is not None:
                    if device_tag == uid or device_tag == devip or device_tag == fuid:
                        print("{}Device was found: {}{}".format(Colors.OK, device_tag, Colors.NC))
                        ConnectionData.HOST = devip
                        device_was_found = True
                        break
            if not device_was_found:
                # Print available device info
                print("{}[i]         FUID        IP               UID{}".format(Colors.OKGREEN, Colors.NC))
                for index, device in enumerate(ConnectionData.MICROS_DEV_IP_DICT.keys()):
                    uid = device
                    devip = ConnectionData.MICROS_DEV_IP_DICT[device][0]
                    fuid = ConnectionData.MICROS_DEV_IP_DICT[device][2]
                    print("[{}{}{}] Device: {}{}{} - {} - {}".format(Colors.BOLD, index, Colors.NC,
                                                                         Colors.OKBLUE, fuid, Colors.NC,
                                                                         devip, uid))

                    device_choose_list.append(devip)
                    device_fid_in_order.append(fuid)
                if len(device_choose_list) > 1:
                    index = int(input("{}Choose a device index: {}".format(Colors.OK, Colors.NC)))
                    ConnectionData.HOST = device_choose_list[index]
                    device_fid = device_fid_in_order[index]
                    print("Device IP was set: {}".format(ConnectionData.HOST))
                else:
                    print("{}Device not found.{}".format(Colors.ERR, Colors.NC))
                    sys.exit(0)
        return ConnectionData.HOST, device_fid


    @staticmethod
    def nodes_status():
        spr_offset1 = 30
        spr_offset2 = 57
        nodes_dict = ConnectionData.read_micrOS_device_cache()
        spacer1 = " " * (spr_offset1-14)
        print("{cols}       [ UID ]{spr1}[ FUID ]\t\t[ IP ]\t\t[ STATUS ]\t[ VERSION ]\t[COMM SEC]{cole}"
              .format(spr1=spacer1, cols=Colors.OKBLUE+Colors.BOLD, cole=Colors.NC))
        for uid, data in nodes_dict.items():
            ip = data[0]
            fuid = "{}{}{}".format(Colors.HEADER, data[2], Colors.NC)
            if uid not in ['__devuid__']:
                spacer1 = " "*(spr_offset1 - len(uid))

                # print status msgs
                is_online = "{}ONLINE{}".format(Colors.OK, Colors.NC) if nwscan.node_is_online(ip, port=ConnectionData.PORT) else "{}OFFLINE{}".format(Colors.WARN, Colors.NC)
                version_data = '<n/a>'
                elapsed_time = 'n/a'

                # is online
                if 'ONLINE' in is_online:
                    # get version data
                    try:
                        start_comm = time.time()
                        version_data = SocketDictClient(host=ip, port=ConnectionData.PORT, silent_mode=True).non_interactive(['version'])
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


def socket_commandline_args(arg_list):
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
    if len(arg_list) > 0 and "man" in arg_list[0]:
        print("--scan / scan\t\t- scan devices")
        print("--dev / dev\t\t- select device - value should be: fuid or uid or devip")
        print("--stat / stat\t\t- show devides online/offline - and memory data")
        print("HINT\t\t- In non interactive mode you can pipe commands with <a> separator")
        sys.exit(0)
    return arg_list, return_action_dict


def main(args, timeout=3):
    """ main connection wrapper function """
    answer_msg = None
    socketdictclient = None
    try:
        socketdictclient = SocketDictClient(host=ConnectionData.HOST, port=ConnectionData.PORT, tout=timeout)
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
        if "Connection reset by peer" not in str(e):
            print("FAILED TO START: " + str(e))
        return False, answer_msg


def run(arg_list=[]):
    """ Run from code
        - Handles extra command line arguments
    """
    args, action = socket_commandline_args(arg_list)
    ConnectionData.auto_execute(search=action['search'], status=action['status'],  dev=action['device_tag'])
    return main(args)


if __name__ == "__main__":
    """Runs in individual - direct execution mode"""
    args, action = socket_commandline_args(sys.argv[1:])
    ConnectionData.auto_execute(search=action['search'], status=action['status'], dev=action['device_tag'])
    main(args)
