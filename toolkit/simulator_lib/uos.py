import os
import stat as py_fs_stat

# https://docs.micropython.org/en/v1.9.2/pyboard/library/uos.html
# https://docs.micropython.org/en/v1.18/library/os.html

MOCK_SIM = False

def listdir(path=None):
    if path is None:
        return os.listdir()
    path = __mock_sim_dir(path)
    print(f"[uos.SIM] listdir: {path}")
    return os.listdir(path)


def getcwd():
    _cwd = os.getcwd()
    if MOCK_SIM:
        cwd = f"{_cwd}/../workspace/simulator/"
        print(f"MOCK PATH: {cwd}")
    elif "workspace/simulator" not in _cwd:
        cwd = f"{_cwd}/toolkit/workspace/simulator/"
        print(f"[uos.SIM] MOCK PATH: {_cwd} -> {cwd}")
    else:
        cwd = _cwd
    return cwd


def __mock_sim_dir(path):
    """
    micropython sim hack
    """
    if MOCK_SIM:
        cwd = getcwd()
        path = f"{cwd}{path}"
        print(f"[!!!] [uos.SIM] CWD PATH HACK: {path}")
    elif "workspace/simulator" not in path:
        path = f"{getcwd()}{path}"
    return path


def ilistdir(path):
    buffer = []
    for filename in listdir(path):
        _name, _type, _inode = filename, stat(f"{path}/{filename}")[0], 0
        print(f"[uos.SIM] ilistdir {path}: ({_name}, {_type:#x}, {_inode}")
        buffer.append((_name, _type, _inode))
    return tuple(buffer)


def mkdir(path):
    print(f"[uos.SIM] mkdir: {path}")
    return os.mkdir(path)


def remove(path):
    path = __mock_sim_dir(path)
    print(f"[uos.SIM] remove: {path}")
    if "simulator" in path and path.replace('/', '').endswith('simulator'):
        print(f"\t[uos.SIM] rmdir: Invalid path! {path}")
        return False
    return os.remove(path)


def rename(old_path, new_path):
    old_path, new_path = __mock_sim_dir(old_path),  __mock_sim_dir(new_path)
    print(f"[uos.SIM] rename: {old_path} -> {new_path}")
    os.rename(old_path, new_path)

def _stat_eval(stat_result):
    """
    micropython converter
    """
    micropython_file_identifier = {'dir': 0x4000, 'file': 0x8000}
    # Check if it's a file
    if py_fs_stat.S_ISREG(stat_result.st_mode):
        # FILE
        return (micropython_file_identifier['file'],)
    if py_fs_stat.S_ISDIR(stat_result.st_mode):
        # DIRECTORY
        return (micropython_file_identifier['dir'],)
    return (0x0,)

def stat(path):
    path = __mock_sim_dir(path)
    stat_result = os.stat(path)
    micropython_stat_result = _stat_eval(stat_result)
    path_type = 'dir' if micropython_stat_result[0] & 0x4000 else 'file'
    print(f"[uos.SIM] stat: {path} {path_type}({micropython_stat_result[0]:#x})")
    return micropython_stat_result


def rmdir(path):
    print(f"[uos.SIM] rmdir: {path}")
    if "simulator" in path and path.replace('/', '').endswith('simulator'):
        print(f"\t[uos.SIM] rmdir: Invalid path! {path}")
        return False
    return os.rmdir(path)


def statvfs(path=None):
    if path is None:
        return os.statvfs(__mock_sim_dir(path))
    return os.statvfs(path)


def uname():
    return os.uname()


def sync():
    print("[uos.SIM] sync - dummy")


def urandom(n):
    print(f"[uos.SIM] sync {n}")
    return os.urandom(n)


def dupterm(stream_object):
    print("[uos.SIM] dupterm - dummy")


def mount(*args, **kwargs):
    print("[uos.SIM] mount - dummy")


def umount(*args, **kwargs):
    print("[uos.SIM] unmount - dummy")


if __name__  == "__main__":
    MOCK_SIM = True
    print(f"SIM root (mock: {MOCK_SIM}): {__mock_sim_dir('/')}\ngetcwd: {getcwd()}")
    print(listdir("/"))
    print(stat('/'))
    print(ilistdir('/'))