#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ipaddress
import socket
import netifaces
import netaddr
import threading
import time
import platform
import sys
import os


MYPATH = os.path.dirname(__file__)
print("Module [SearchDevices] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYPATH))
try:
    from . import LocalMachine
    CommandHandler = LocalMachine.CommandHandler
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    sys.path.append(MYPATH)
    from LocalMachine import CommandHandler


print("Module [SearchDevices] path: {} __package__: {} __name__: {}".format(sys.path[0], __package__, __name__))
try:
    from . import LocalMachine
    CommandHandler = LocalMachine.CommandHandler
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    sys.path.append(sys.path[0])
    from LocalMachine import CommandHandler


AVAILABLE_DEVICES_LIST = []


def add_element_to_list(element):
    global AVAILABLE_DEVICES_LIST
    if element not in AVAILABLE_DEVICES_LIST:
        AVAILABLE_DEVICES_LIST.append(element)


def get_all_hosts(net, subnet=24):
    """
    Generate network range list for scanning
    """
    # Prompt the user to input a network address
    net_addr = '{net}/{subnet}'.format(net=net, subnet=subnet)
    # Create the network
    ip_net = ipaddress.ip_network(net_addr)
    # Get all hosts on that network
    all_hosts = list(ip_net.hosts())
    return all_hosts[1:-1]


def my_local_ip():
    """
    Get local machine local IP
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    return local_ip


def gateway_ip():
    """
    Get router IP
    """
    gws = netifaces.gateways()
    return list(gws['default'].values())[0][0]


def guess_net_address(gateway_ip, subnet=24):
    """
    Determine network IP
    """
    ip = netaddr.IPNetwork('{gw_ip}/{subnet}'.format(gw_ip=gateway_ip, subnet=subnet))
    return ip.network


def __worker_filter_online_devices(host_list, port, thname="main"):
    """
    Get online devices from network range
    """
    global AVAILABLE_DEVICES_LIST
    for host in host_list:
        host = str(host)
        command = "ping {ip} -n 1".format(ip=host) if platform.system().lower()=='windows' else "ping -c 1 -p {port} {ip}".format( port=port, ip=host)
        exitcode, stdout, stderr = CommandHandler.run_command(command, shell=True)
        if exitcode == 0 and 'unreachable' not in stdout.lower():
            print("[{}] ONLINE: {}".format(thname, host))
            add_element_to_list(host)
        else:
            print("[{}] OFFLINE: {}".format(thname, host))


def filter_threads(host_list, port, threads=80):
    """
    Use threads for parallel network scanning
    """
    thread_instance_list = []
    range_size = len(host_list) / threads
    for cnt in range(1, threads+1):
        start_index = round((cnt-1)*range_size)
        end_index = round(cnt*range_size)
        #print("RANGE: {} - {}".format(start_index, end_index))
        host_range = host_list[start_index:end_index]
        thread_name = "thread-{}-[{}-{}]".format(cnt, start_index, end_index)
        thread_instance_list.append(
            threading.Thread(target=__worker_filter_online_devices, args=(host_range, port, thread_name,))
        )

    for mythread in thread_instance_list:
        mythread.start()

    for mythread in thread_instance_list:
        mythread.join()

    print("{} device was found: {}".format(len(AVAILABLE_DEVICES_LIST), AVAILABLE_DEVICES_LIST))
    return AVAILABLE_DEVICES_LIST


def online_device_scanner(service_port=9008):
    start_time = time.time()

    gw_ip = gateway_ip()
    net_ip = guess_net_address(gw_ip)
    all_hosts_in_net_list = get_all_hosts(net_ip)
    online_devices = filter_threads(all_hosts_in_net_list, port=service_port)

    end_time = time.time()
    print("Elapsed time: {}".format(end_time - start_time))

    return online_devices


def node_is_online(ip, port=9008):
    cmd_base = 'ping -c 1 -p {port} {ip}'
    cmd = cmd_base.format(port=port, ip=ip)
    exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(cmd, shell=True, debug=False)
    if exitcode == 0 and len(stderr.strip()) == 0:
        return True
    else:
        return False


if __name__ == "__main__":
    online_device_scanner()

