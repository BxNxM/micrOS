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
import concurrent.futures

MYDIR = os.path.dirname(__file__)
print("Module [socketClient] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYDIR))
try:
    from .lib import SearchDevices
    from .lib.TerminalColors import Colors
    from .lib.LocalMachine import FileHandler
    from .lib.micrOSClient import micrOSClient
    from .lib.micrOSClient import micros_connection_metrics
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    import lib.SearchDevices as SearchDevices
    from lib.TerminalColors import Colors
    from lib.LocalMachine import FileHandler
    from lib.micrOSClient import micrOSClient
    from lib.micrOSClient import micros_connection_metrics


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
                if not (ip.startswith('10.') or ip.startswith('192.') or ip.startswith('172.')):
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
        if len(uid_list_to_select) > 1 and device_tag is None:
            index = int(input("{}Choose a device index: {}".format(Colors.OK, Colors.NC)))
            device = ConnectionData.MICROS_DEVICES[uid_list_to_select[index]]
            print("Device was selected: {}".format(device))
            # IP, PORT, FID, UID
            return device[0], device[1], device[2], uid_list_to_select[index]
        else:
            print("{}Device not found.{}".format(Colors.ERR, Colors.NC))
            return None, None, None, None

    @staticmethod
    def nodes_status():
        spr_offset1 = 30
        spr_offset2 = 57

        def _dev_status(ip, port, fuid, uid):
            fuid = "{}{}{}".format(Colors.HEADER, fuid, Colors.NC)
            if uid not in ['__devuid__']:
                spacer1 = " " * (spr_offset1 - len(uid))

                # print status msgs
                is_online = "{}ONLINE{}".format(Colors.OK, Colors.NC) if SearchDevices.node_is_online(ip, port=port) else "{}OFFLINE{}".format(
                    Colors.WARN, Colors.NC)
                version_data = '<n/a>'
                elapsed_time = 'n/a'
                online_ip = None

                # is online
                if 'ONLINE' in is_online:
                    # get version data
                    online_ip = ip
                    try:
                        start_comm = time.time()
                        version_data = SocketDictClient(host=ip, port=port, silent_mode=True, tout=3).non_interactive(['version'])
                        elapsed_time = "{:.3f}".format(time.time() - start_comm)
                    except:
                        pass

                # Generate line printout
                base_info = "{uid}{spr1}{fuid}".format(uid=uid, spr1=spacer1, fuid=fuid)
                spacer1 = " " * (spr_offset2 - len(base_info))
                data_line_str = "{base}{spr2}{ip}\t{stat}\t\t{version}\t\t{elapt}" \
                    .format(base=base_info, spr2=spacer1, ip=ip,
                            stat=is_online, version=version_data, elapt=elapsed_time)
                return data_line_str, online_ip
            return None

        nodes_dict = ConnectionData.read_micrOS_device_cache()
        spacer1 = " " * (spr_offset1 - 14)
        print("{cols}       [ UID ]{spr1}[ FUID ]\t\t[ IP ]\t\t[ STATUS ]\t[ VERSION ]\t[COMM SEC]{cole}"
              .format(spr1=spacer1, cols=Colors.OKBLUE + Colors.BOLD, cole=Colors.NC))

        # Start parallel status queries
        query_list = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for uid, data in nodes_dict.items():
                ip = data[0]
                port = data[1]
                fuid = data[2]
                future = executor.submit(_dev_status, ip, port, fuid, uid)
                query_list.append(future)

        online_ip_addr_list = []
        for q in query_list:
            res = q.result()
            if res is None:
                continue
            data_line_str, ipaddr = res
            # Print command line status
            print(data_line_str)
            if isinstance(ipaddr, str):
                online_ip_addr_list.append(ipaddr)
        return online_ip_addr_list

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

    def __init__(self, host='localhost', port=9008, silent_mode=False, tout=4):
        self.silent_mode = silent_mode
        self.host = host
        self.port = port
        self.tout = tout
        self.client = micrOSClient(self.host, self.port, dbg=False)         # <== SET CLIENT DEBUG HERE

    def run_command(self, cmd):
        data = self.client.send_cmd_retry(cmd)
        return data

    def interactive(self):
        return self.client.telnet()

    def non_interactive(self, cmd_list, separator='<a>', to_str=True):
        #print("non_interactive input: {}".format(cmd_list))
        cmd_args = cmd_list
        if isinstance(cmd_list, str):
            cmd_args = cmd_list.split(separator)
        elif isinstance(cmd_list, list) or isinstance(cmd_list, tuple):
            if len(cmd_list) == 1:
                if separator in cmd_list[0]:
                    cmd_args = cmd_list[0].split(separator)
        if separator in cmd_args:
            cmd_args.remove(separator)
        ret_list = self.command_pipeline(cmd_args)
        if to_str:
            ret_msg = ""
            for ret in ret_list:
                if ret is not None:
                    ret_msg += '\n'.join(ret).strip()
            if not self.silent_mode:
                print(ret_msg)
            return ret_msg
        return ret_list

    def command_pipeline(self, cmd_pipeline):
        ret_msg = []
        # Start connection - ensure it stays open
        self.client.connect(self.tout)
        for cmd in cmd_pipeline:
            cmd = cmd.strip()
            # Run commands over tcp/ip
            data = self.run_command(cmd)
            if data is not None:
                ret_msg.append(data)
        # Close connection, all cmd was sent
        self.client.close()
        return ret_msg

#########################################################
#                       MAIN                            #
#########################################################


def main(args, host='127.0.0.1', port=9008, timeout=3):
    """ main connection wrapper function """
    answer_msg = None

    try:
        socketdictclient = SocketDictClient(host=host, port=port, tout=timeout)
        if len(args) == 0:
            #print("Run interactive mode")
            # INTERACTIVE MODE
            socketdictclient.interactive()
        else:
            #print("Run non-interactive mode")
            # NON INTERACTIVE MODE WITH ARGS
            answer_msg = socketdictclient.non_interactive(args)
        return True, answer_msg
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print("Socket communication error (tout: {}): {}".format(timeout, e))
        if "timed out" in str(e) or "Host is down" in str(e):
            raise Exception("TimeOut")
    return False, answer_msg


def socket_commandline_args(arg_list):
    return_action_dict = {'search': False, 'device_tag': None, 'status': False}
    if len(arg_list) > 0 and (arg_list[0].startswith('--scan') or arg_list[0].startswith('scan')):
        del arg_list[0]
        return_action_dict['search'] = True
    if len(arg_list) > 0 and (str(arg_list[0]).startswith('--stat') or str(arg_list[0]).startswith('stat')):
        del arg_list[0]
        return_action_dict['status'] = True
    if len(arg_list) > 0 and "dev" in arg_list[0]:
        return_action_dict['device_tag'] = arg_list[1]
        del arg_list[0:2]
    if len(arg_list) > 0 and arg_list[0].startswith('clean'):
        ConnectionData.clean_cache()
        sys.exit()
    if len(arg_list) > 0 and arg_list[0].startswith('list'):
        ConnectionData.list_devices()
        sys.exit()
    if len(arg_list) > 0 and ("man" == arg_list[0] or "manual" == arg_list[0] or "hint" in arg_list[0]):
        print("--scan / scan\t\t- scan devices")
        print("--dev / dev\t\t- select device - value should be: fuid or uid or devip")
        print("--stat / stat\t\t- show devides online/offline - and memory data")
        print("--clean / clean\t\t- clean device_conn_cache.json")
        print("--list / list\t\t- list mocrOS devices")
        print("HINT\t\t- In non interactive mode you can pipe commands with <a> separator")
        sys.exit(0)
    return arg_list, return_action_dict


def run(arg_list=[], timeout=5):
    """ Run from code
        - Handles extra command line arguments
    """
    #print("Socket run (raw): {}".format(arg_list))
    args, action = socket_commandline_args(arg_list)
    host, port, fid, uid = ConnectionData.auto_execute(search=action['search'], status=action['status'], dev=action['device_tag'])
    output = False, ''
    try:
        output = main(args, host=host, port=port, timeout=timeout)
    except Exception as e:
        if "TimeOut" in str(e):
            print("Resolve device by host ... {}.local {}:{}:{}".format(fid, host, port, uid))
            # host, port, fid, uid
            ConnectionData.resolve_hostname(fid, uid)
    return output


def connection_metrics(host):
    return micros_connection_metrics(address=host)


if __name__ == "__main__":
    """Runs in individual - direct execution mode"""
    arg_list = sys.argv[1:]
    run(arg_list=arg_list)
