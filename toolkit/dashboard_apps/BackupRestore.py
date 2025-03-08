#!/usr/bin/env python3

import os
import sys
import json
MYPATH = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(MYPATH, "../user_data/node_config_archive/")
sys.path.append(os.path.join(MYPATH, '../lib/'))
from TerminalColors import Colors

try:
    from ._app_base import AppBase
except:
    from _app_base import AppBase

CLIENT = None


###########################################################
def _value_type(value):
    value = value.strip()
    if value == "True":     # Bool
        return True
    if value == "False":    # Bool
        return False
    try:
        value = int(value)  # integer
        return value
    except Exception:
        pass
    return value            # string


def backup():
    device = CLIENT.get_device()
    print(f"\tBackup name format: {device}-<tag>-node_config.json")
    print(f"\t\t tag is optional (press simply enter): {device}-node_config.json")
    backup_tag = input(f"\tFill backup tag for {device}: ").strip()
    backup_tag = "" if len(backup_tag) == 0 else f"-{backup_tag}"
    backup_name = f"{device}{backup_tag}-node_config.json"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    print(f"\tBackup path: {backup_path}")

    status, answer = CLIENT.run(["conf", "dump"])
    if status:
        configuration = {line.split(":")[0].strip(): _value_type(':'.join(line.split(":")[1:])) for line in answer.strip().split("\n") if ":" in line}
        with open(backup_path, 'w') as f:
            f.write(json.dumps(configuration, indent=4))
    else:
        print(f"{Colors.ERR} Cannot get node config:{Colors.NC} {status}: {answer}")
    print(f"{Colors.OKGREEN}Backup was successfully saved:{Colors.NC} {backup_path}")


def restore():
    device = CLIENT.get_device()
    print(f"\tRestore backup for: {device}")
    diff_config = {}

    # SELECT AND LOAD CONFIG BACKUP
    backup_list = os.listdir(BACKUP_DIR)
    for i, json_backup in enumerate(backup_list):
        print(f"[{i}]  {json_backup}")
    opt = input("Select backup number to restore: ")
    try:
        opt = int(opt)
    except Exception as e:
        print(f"{Colors.ERR}INVALID INDEX:{Colors.NC} {e}")
        return
    backup_path = os.path.join(BACKUP_DIR, backup_list[opt])
    with open(backup_path, 'r') as f:
        backup_dict = json.load(f)
    print(f"SELECTED CONFIG: {backup_path}")
    print(f"BACKUP CONFIG DICT:\n{backup_dict}")

    # LOAD LIVE DEVICE CONFIG - create config diff
    status, answer = CLIENT.run(["conf", "dump"])
    if not status:
        return f"Cannot load live device config"
    live_configuration = {line.split(":")[0].strip(): _value_type(':'.join(line.split(":")[1:])) for line in answer.strip().split("\n") if ":" in line}

    for key, live_value in live_configuration.items():
        if key in ("version", "devip", "hwuid", "version", "devfid"):   # IGNORE KEYS
            continue
        bckp_value = backup_dict.get(key, None)
        if bckp_value is None or bckp_value == live_value:
            continue
        print(f"\tDIFF: {key} : {live_value} -> {bckp_value}")
        diff_config[key] = bckp_value

    if len(diff_config.keys()) == 0:
        print(f"{Colors.OKGREEN}No diff in config - skip restore{Colors.NC}")
        return
    verify = input(f"{Colors.WARN}APPLY DIFFS?{Colors.NC} [Y/n]: ")
    if verify != "Y":
        print(f"{Colors.WARN}SKIP restore...{Colors.NC}")
        return

    print(f"PACKAGE CONFIG DIFFS...{device}")
    conf_cmd_list = ["conf"]
    for key, value in diff_config.items():
        print(f"\tADD {key} : {value}")
        conf_cmd_list.append(f"{key} {value}")
    conf_cmd_list.append("reboot")

    # Restore
    print(f"APPLY CONFIG DIFFS...{device}")
    status, answer = CLIENT.run(conf_cmd_list)
    if status:
        print(f"{Colors.OKGREEN}Backup was successfully restored:{Colors.NC} {backup_path}\nRebooting...")
    else:
        print(f"{Colors.ERR}Restore error:{Colors.NC} {status}: {answer}")



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
    global CLIENT
    CLIENT = AppBase(device=devfid, password=pwd)

    print(f"{Colors.WARN}Backup & Restore management{Colors.NC}\n")
    while True:
        print(f"{Colors.UNDERLINE}Operations on {CLIENT.get_device()}{Colors.NC}")
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
