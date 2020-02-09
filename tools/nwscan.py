import os

def map_wlan_devices():
    devices = []
    for device in os.popen('arp -a'): devices.append([device.split(' ')[1][1:-1], device.split(' ')[3]])
    return devices
