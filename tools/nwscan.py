import os
import sys
MYPATH = os.path.dirname(os.path.abspath(__file__))
API_DIR_PATH = os.path.join(MYPATH, 'MicrOSDevEnv/')
sys.path.append(API_DIR_PATH)
import LocalMachine


def map_wlan_devices():
    print("Find devices connected to the network... [arp -a]")
    devices = []
    exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command('arp -a', shell=True)
    if exitcode == 0:
        for device in stdout.split('\n'):
            try:
                devip = device.split(' ')[1][1:-1]
                macaddr = device.split(' ')[3]
                devices.append([devip, macaddr])
            except:
                pass
    return devices


def filter_by_open_port(device_ip_list, port=9008):
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

