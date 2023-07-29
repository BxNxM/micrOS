#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ipaddress
import socket
import netaddr
import time
import sys
import os
import concurrent.futures


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


def __get_all_hosts(net, subnet=24):
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
    h_name = socket.gethostname()
    ip_address = socket.gethostbyname(h_name)
    return ip_address


def __gateway_ip():
    """
    Get router IP
    """
    # Create a temporary UDP socket
    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    temp_socket.connect(("8.8.8.8", 80))  # Connecting to a known external IP

    # Retrieve the local IP address
    local_ip_address = temp_socket.getsockname()[0]
    temp_socket.close()

    ip_addr_hack = local_ip_address.split('.')
    ip_addr_hack[-1] = '1'
    local_ip_address = '.'.join(ip_addr_hack)
    local_ip_address = ipaddress.ip_address(local_ip_address)
    return local_ip_address


def __guess_net_address(gateway_ip, subnet=24):
    """
    Determine network IP
    """
    ip = netaddr.IPNetwork('{gw_ip}/{subnet}'.format(gw_ip=gateway_ip, subnet=subnet))
    return ip.network


def __port_is_open_ip_filter(host_list, port, thname="main"):
    """
    Get online devices from network range
    """
    # Elemental port check on ip
    def isOpen(_host, _port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        socket.setdefaulttimeout(1)
        conn = sock.connect_ex((_host, _port))
        _is_open = conn == 0
        sock.close()
        return _is_open, _host

    # Search threads
    is_online_threads = []
    online_host_list = []
    timeout = len(host_list) * 2
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for host in host_list:
            host = str(host)
            f = executor.submit(isOpen, host, port)
            is_online_threads.append(f)

    for query_obj in is_online_threads:
        try:
            is_open, host = query_obj.result(timeout)
        except:
            continue
        if is_open:
            print("[{}] ONLINE: {}".format(thname, host))
            online_host_list.append(host)
        else:
            print("\t[{}] OFFLINE: {}".format(thname, host))
    return online_host_list


def __ip_scanner_on_open_port(host_list, port, threads=50):
    """
    Use threads for parallel network scanning
    """
    thread_instance_list = []
    range_size = len(host_list) / threads
    online_devices = []

    # Start parallel status queries
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for cnt in range(1, threads + 1):
            start_index = round((cnt - 1) * range_size)
            end_index = round(cnt * range_size)
            host_range = host_list[start_index:end_index]
            thread_name = "thread-{}-[{}-{}]".format(cnt, start_index, end_index)

            future = executor.submit(__port_is_open_ip_filter, host_range, port, thread_name)
            thread_instance_list.append(future)

        # Collect results from port filtering
        for query in thread_instance_list:
            try:
                online_dev_ip_list = query.result(10)
            except:
                continue
            if len(online_dev_ip_list) > 0:
                online_devices = list(set(online_devices + online_dev_ip_list))

    print("{} device was found: {}".format(len(online_devices), online_devices))
    return online_devices


def online_device_scanner(service_port=9008):
    start_time = time.time()

    gw_ip = __gateway_ip()
    net_ip = __guess_net_address(gw_ip)
    all_hosts_in_net_list = __get_all_hosts(net_ip)
    online_devices = __ip_scanner_on_open_port(all_hosts_in_net_list, port=service_port)

    end_time = time.time()
    print("Elapsed time: {} sec".format(round(end_time - start_time)))

    return online_devices


def node_is_online(ip, port=9008):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.setdefaulttimeout(1)
    conn = sock.connect_ex((ip, port))
    is_open = conn == 0
    sock.close()
    return is_open


if __name__ == "__main__":
    online_devices = online_device_scanner()
    print(f"Online devices: {online_devices}")
    print(f"Device {online_devices[0]} is online?: {node_is_online(ip=online_devices[0])}")

