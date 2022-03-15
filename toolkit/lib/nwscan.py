#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import os

MYPATH = os.path.dirname(__file__)
print("Module [nwscan] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYPATH))
try:
    from . import LocalMachine
    from . import SearchDevices
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    sys.path.append(MYPATH)
    import LocalMachine
    import SearchDevices


def map_wlan_devices(service_port=9008):
    devices = []
    print("[NWSCN] Get online host list on port {}".format(service_port))
    host_address_list = SearchDevices.online_device_scanner(service_port=service_port)
    print("[NWSCN] Get macaddress by ip ...")
    for device in host_address_list:
        devip = device
        macaddr = "n/a"
        try:
            exitcode, stdout, stderr = LocalMachine.run_command('arp -n {}'.format(device), shell=True, debug=False)
            if exitcode == 0:
                macaddr = stdout.split(' ')[3]
        except Exception:
            pass
        devices.append([devip, macaddr])
    return devices


def filter_by_open_port(device_ip_list, port=9008):
    """Obsolete"""
    print("Filter devices by (micrOS) open port...  [ping -c 2 -p {port} <ip>]".format(port=port))
    devices = []
    cmd_base = 'ping -c 1 -p {port} {ip}'
    for device in device_ip_list:
        devip = device[0]
        cmd = cmd_base.format(port=port, ip=devip)
        exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(cmd, shell=True)
        if exitcode == 0 and len(stderr.strip()) == 0:
            devices.append(device)
    return devices


def node_is_online(ip, port=9008):
    cmd_base = 'ping -c 1 -p {port} {ip}'
    cmd = cmd_base.format(port=port, ip=ip)
    exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(cmd, shell=True, debug=False)
    if exitcode == 0 and len(stderr.strip()) == 0:
        return True
    else:
        return False


if __name__ == "__main__":
    device_list = map_wlan_devices()
    filtered_device_list = filter_by_open_port(device_ip_list=device_list)
    for dev in filtered_device_list: print(dev)

