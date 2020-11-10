import os
import sys
MYPATH = os.path.dirname(os.path.abspath(__file__))
API_DIR_PATH = os.path.join(MYPATH, 'MicrOSDevEnv/')
sys.path.append(API_DIR_PATH)
import LocalMachine
import SearchDevices


def map_wlan_devices(service_port=9008):
    devices = []
    host_address_list = SearchDevices.online_device_scanner(service_port=service_port)
    for device in host_address_list:
        devip = device
        macaddr = "n/a"
        try:
            exitcode, stdout, stderr = LocalMachine.run_command('arp -n {}'.format(device), shell=True)
            if exitcode == 0:
                macaddr = stdout.split(' ')[3]
        except Exception:
            pass
        devices.append([devip, macaddr])
    return devices


def filter_by_open_port(device_ip_list, port=9008):
    """Obsolete"""
    print("Filter devices by (MicrOS) open port...  [ping -c 2 -p {port} <ip>]".format(port=port))
    devices = []
    cmd_base = 'ping -c 2 -p {port} {ip}'
    for device in device_ip_list:
        devip = device[0]
        cmd = cmd_base.format(port=port, ip=devip)
        exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(cmd, shell=True)
        if exitcode == 0 and len(stderr.strip()) == 0:
            devices.append(device)
    return devices


def node_is_online(ip, port=9008):
    cmd_base = 'ping -c 2 -p {port} {ip}'
    cmd = cmd_base.format(port=port, ip=ip)
    exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(cmd, shell=True)
    if exitcode == 0 and len(stderr.strip()) == 0:
        return True
    else:
        return False


if __name__ == "__main__":
    device_list = map_wlan_devices()
    filtered_device_list = filter_by_open_port(device_ip_list=device_list)
    for dev in filtered_device_list: print(dev)

