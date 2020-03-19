#!/usr/bin/env python3

import os
import sys
MYPATH = os.path.dirname(os.path.abspath(__file__))
SOCKET_CLIENT_DIR_PATH = os.path.join(MYPATH, 'tools/')
API_DIR_PATH = os.path.join(MYPATH, 'tools/MicrOSDevEnv/')
sys.path.append(API_DIR_PATH)
sys.path.append(SOCKET_CLIENT_DIR_PATH)
import argparse
import MicrOSDevEnv
import socketClient

def arg_parse():
    parser = argparse.ArgumentParser(prog="MicrOS dev toolkit - deploy, connect, update, etc.", \
                                     description="CMDline wrapper for {}".format(API_DIR_PATH, 'MicrOSDevEnv.py'))
    parser.add_argument("-m", "--make", action="store_true", help="Erase & Deploy & Precompile (MicrOS) & Install (MicrOS)")
    parser.add_argument("-r", "--update", action="store_true", help="Update/redeploy connected (usb) MicrOS. \
                                                                    - node config will be restored")
    parser.add_argument("-c", "--connect", action="store_true", help="Connect via socketclinet")
    parser.add_argument("-p", "--connect_parameters", type=str, help="Parameters for connection in non-interactivve mode.")

    group = parser.add_argument_group("Development & Deployment")
    group.add_argument("-e", "--erase", action="store_true", help="Erase device")
    group.add_argument("-d", "--deploy", action="store_true", help="Deploy micropython")
    group.add_argument("-i", "--install", action="store_true", help="Install MicrOS on micropython")
    group.add_argument("-l", "--list_devs_n_bins", action="store_true", help="List connected devices & micropython binaries.")
    group.add_argument("-cc", "--cross_compile_micros", action="store_true", help="Cross Compile MicrOS system [py -> mpy]")
    group.add_argument("-v", "--version", action="store_true", help="Get micrOS version - repo + connected device.")

    group2 = parser.add_argument_group("Connection")
    group2.add_argument("-u", "--connect_via_usb", action="store_true", help="Connect via serial port - usb")

    group3 = parser.add_argument_group("Toolkit development")
    group3.add_argument("--dummy", action="store_true", help="Skip subshell executions - for API logic test.")

    args = parser.parse_args()
    return args

def list_devs_n_bins(api_obj):
    dev_list = api_obj.micros_devices
    bin_list = api_obj.micropython_bins_list
    print("Devices:")
    for dev in dev_list:
        print("\t{}".format(dev))
    print("Micropython binaries:")
    for bin_ in bin_list:
        print("\t{}".format(bin_))

def make(api_obj):
    api_obj.deploy_micros()

def erase(api_obj):
    api_obj.erase_dev()

def deploy(api_obj):
    api_obj.deploy_micropython_dev()

def install(api_obj):
    api_obj.put_micros_to_dev()

def connect(args=None):
    if args is not None and len(args) != 0:
        socketClient.run(arg_list=args.split(' '))
    else:
        socketClient.run(arg_list=[])

def precompile_micrOS(api_obj):
    api_obj.precompile_micros()

def connect_via_usb(api_obj):
    api_obj.connect_dev()

def get_MicrOS_version(api_obj):
    print(api_obj.get_micrOS_version())


def update_micrOS_on_node(api_obj):
    api_obj.update_micros_via_usb()

if __name__ == "__main__":
    cmd_args = arg_parse()

    # Create API object ()
    if cmd_args.dummy:
        api_obj = MicrOSDevEnv.MicrOSDevTool(dummy_exec=True)
    else:
        api_obj = MicrOSDevEnv.MicrOSDevTool()

    # Commands
    if cmd_args.list_devs_n_bins:
        list_devs_n_bins(api_obj)

    if cmd_args.make:
        make(api_obj)

    if cmd_args.erase:
        erase(api_obj)

    if cmd_args.deploy:
        deploy(api_obj)

    if cmd_args.install:
        install(api_obj)

    if cmd_args.connect:
        connect(args=cmd_args.connect_parameters)

    if cmd_args.connect_via_usb:
        connect_via_usb(api_obj)

    if cmd_args.cross_compile_micros:
        precompile_micrOS(api_obj)

    if cmd_args.version:
        get_MicrOS_version(api_obj)

    if cmd_args.update:
        update_micrOS_on_node(api_obj)

