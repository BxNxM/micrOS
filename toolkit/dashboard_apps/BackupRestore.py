#!/usr/bin/env python3

import os
import sys
import time
import json
MYPATH = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(MYPATH, "../user_data/node_config_archive/")
sys.path.append(os.path.dirname(MYPATH))
import socketClient
sys.path.append(os.path.join(MYPATH, '../lib/'))
from TerminalColors import Colors

# FILL OUT
DEVICE = 'node01'
PASSWD = None

def base_cmd():
    if PASSWD is None:
        return ['--dev', DEVICE]
    return ['--dev', DEVICE, '--password', PASSWD]


def run_command(cmd):
    # EDIT YOUR COMMAND
    args = base_cmd() + cmd
    status, answer = socketClient.run(args)
    return status, answer

###########################################################

def backup():
    print(f"\tBackup name format: {DEVICE}-<tag>-node_config.json")
    print(f"\t\t tag is optional (press simply enter): {DEVICE}-node_config.json")
    backup_tag = input(f"\tFill backup tag for {DEVICE}: ").strip()
    backup_tag = "" if len(backup_tag) == 0 else f"-{backup_tag}"
    backup_name = f"{DEVICE}{backup_tag}-node_config.json"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    print(f"\tBackup path: {backup_path}")

    status, answer = run_command(["conf", "dump"])
    if status:
        configuration = {line.split(":")[0].strip(): ''.join(line.split(":")[1:]).strip() for line in answer.strip().split("\n") if ":" in line}
        with open(backup_path, 'w') as f:
            f.write(json.dumps(configuration, indent=4))
    else:
        print(f"{Colors.ERR} Cannot get node config:{Colors.NC} {status}: {answer}")
    print(f"{Colors.OKGREEN}Backup was successfully saved:{Colors.NC} {backup_path}")


def restore():
    print(f"\tRestore backup for: {DEVICE}")
    print("\t|--- TODO")
    # Search backups in BACKUP_DIR
    # Backup selection (load json)
    # Compare live and backup config
    #   Live:     status, answer = run_command(["conf", "dump"])
    # Dump diff
    # Enable restore (verify from user)
    # Restore the changes param by param


def delete_backup():
    backup_list = os.listdir(BACKUP_DIR)
    for i, json_backup in enumerate(backup_list):
        print(f"[{i}]  {json_backup}")
    opt = input("Select backup number to delete: ")
    try:
        opt = int(opt)
    except Exception as e:
        print(f"{Colors.ERR}INVALID INDEX:{Colors.NC} {e}")
        return
    remove_path = os.path.join(BACKUP_DIR, backup_list[opt])
    print(f"Remove: {remove_path}")
    os.remove(remove_path)
    print(f"{Colors.OKGREEN}Backup was successfully deleted{Colors.NC}")

###########################################################


def app(devfid=None, pwd=None):
    """
    devfid: selected device input
        send command(s) over socket connection [socketClient.run(args)]
        list load module commands and send in single connection
    """
    global DEVICE, PASSWD
    if devfid is not None:
        DEVICE = devfid
    if pwd is not None:
        PASSWD = pwd

    print(f"{Colors.WARN}Backup & Restore management{Colors.NC}\n")
    while True:
        print(f"{Colors.UNDERLINE}Operations on {DEVICE}{Colors.NC}")
        print("\t[1]  Backup")
        print("\t[2]  Restore")
        print("\t[3]  Delete backups")
        print("\t[4]  Exit")
        opt = input(f"{Colors.BOLD}Select operation{Colors.NC}: ")
        try:
            opt = int(opt)
        except Exception as e:
            return f"{Colors.ERR}INVALID OPTION:{Colors.NC} {opt}: {e}"
        if opt == 1:
            print(f"{Colors.BOLD}=== BACKUP ==={Colors.NC}")
            backup()
        elif opt == 2:
            print(f"{Colors.BOLD}=== RESTORE ==={Colors.NC}")
            restore()
        elif opt == 3:
            print(f"{Colors.BOLD}=== DELETE ==={Colors.NC}")
            delete_backup()
        elif opt == 4:
            break
        else:
            return f"{Colors.ERR}UNKNOWN OPTION:{Colors.NC} {opt}"
    return f"{Colors.OKGREEN}Bye!{Colors.NC}"


if __name__ == "__main__":
    app()
