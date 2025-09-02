from uos import mount, umount, listdir
from machine import SDCard


def mount_storage():
    if '/sd' in listdir():
        return "Already mounted"
    try:
        mount(SDCard(), "/sd")
    except Exception as e:
        return f"Mount error: {e}"
    return "Mount done"


def unmount_storage():
    try:
        umount("/sd")
    except Exception as e:
        return f"Unmount error: {e}"
    return "Unmount done"


def list_storage():
    return listdir('/sd/')


def write_file(name, content):
    try:
        with open(f'/sd/{name}', 'w') as f:
            f.write(content)
    except Exception as e:
        return f"Write error {name}: {e}"
    return f"Write {name} done"


def read_file(name):
    try:
        with open(f'/sd/{name}', 'r') as f:
            return f.read()
    except Exception as e:
        return f"Read error {name}: {e}"


def help(widgets=False):
    """
    [BETA]
    """
    return "mount_storage", "unmount_storage", "list_storage",\
           "write_file name content", "read_file name"