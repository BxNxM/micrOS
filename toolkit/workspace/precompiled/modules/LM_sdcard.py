from machine import SDCard
from uos import mount, umount
from Files import is_dir, path_join, list_fs, OSPath

STORAGE_PATH = path_join(OSPath.DATA, "storage")

def mount_storage():
    """
    Mount SD Card under /data/storage
    """
    if is_dir(STORAGE_PATH):
        return f"Already mounted: {STORAGE_PATH}"
    try:
        mount(SDCard(), STORAGE_PATH)
    except Exception as e:
        return f"Mount error {STORAGE_PATH}: {e}"
    return f"Mount done: {STORAGE_PATH}"


def unmount_storage():
    """
    Unmount SD Card under /data/storage
    """
    try:
        umount(STORAGE_PATH)
    except Exception as e:
        return f"Unmount error {STORAGE_PATH}: {e}"
    return f"Unmount done: {STORAGE_PATH}"


def list_storage():
    """
    List files/dirs under /data/storage
    """
    return list_fs(STORAGE_PATH)


def write_file(name, content):
    """
    Write a file
    :param name: file name with type
    :param content: file text content
    """
    target = path_join(STORAGE_PATH, name)
    try:
        with open(target, 'w') as f:
            f.write(content)
    except Exception as e:
        return f"Write error {target}: {e}"
    return f"Write done: {target}"


def read_file(name):
    """
    Read a file
    :param name: file name with type
    """
    target = path_join(STORAGE_PATH, name)
    try:
        with open(target, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Read error {target}: {e}"


def help(widgets=False):
    """
    [BETA]
    """
    return "mount_storage", "unmount_storage", "list_storage",\
           "write_file 'f.txt' 'text'", "read_file 'f.txt'"