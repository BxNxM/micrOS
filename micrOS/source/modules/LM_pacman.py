from sys import modules
from Common import socket_stream
from Files import list_fs, ilist_fs, remove_file, remove_dir, OSPath, path_join


#############################################
#     Safe file system handler functions    #
#############################################

def ls(path="/", content='*', raw=False, select='*', core=False):
    """
    Linux like ls command - list app resources and app folders
    :param path: path to list, default: /
    :param content: content type, default all, f-file, d-dir can be selected
    :param raw: keep raw output [(is_app, type), ...]
    :param select: select specific app resource: LM or IO, default: all
    :param core: include core system files
    """
    items = list_fs(path, content, select=select, core=core)
    if raw:
        return items

    # Build a formatted output (just like `ls -l` style index)
    lines = ""
    for i, f in enumerate(items):
        spacer = " " * (4 - len(str(i+1)))
        if content == "*":
            lines += f"{i+1}{spacer}{f[0]}   {f[1]}\n"
        else:
            lines += f"{i + 1}{spacer}{f}\n"
    return lines


def rm(path, force=False):
    """
    Linux like rm command - delete app resources and folders
    :param path: app resource name/path, ex.: LM_robustness.py
    :param force: bypasses protection check - sudo mode
    """
    return remove_file(path, force)


def rmdir(path, force=False):
    """
    Linux like rmdir command for directory deletion
    :param path: app resource folder path, ex.: /lib/myapp
    :param force: bypasses protection check - sudo mode
    """
    return remove_dir(path, force)


def dirtree(path="/", raw=False, core=False):
    """Return only directories from a given path."""
    path = path if path.endswith('/') else f"{path}/"
    folders = [path_join(path, item) for item in ilist_fs(path, type_filter='d', core=core)]
    folder_contents = {folder:list_fs(folder) for folder in folders}
    if raw:
        return folder_contents
    formatted_output = ""
    for k, v in folder_contents.items():
        formatted_output += f"{k}\n"
        for val in v:
            formatted_output += f"\t{val[0]}   {val[1]}\n"
    return formatted_output


def cat(path):
    """
    Dump any file content
    """
    with open(path, 'r') as f:
        content = f.read()
    return content


def download(ref=None):
    """
    OBSOLETED interface
    """
    return install(ref)


def install(ref=None):
    """
    Unified mip-based installer for micrOS.
    Automatically detects:
      1. Official MicroPython packages (from https://micropython.org/pi/v2)
            Example: pacman install "umqtt.simple"
      2. Single-file load modules (LM_/IO_ names or URLs)
            Example: pacman install "https://github.com/BxNxM/micrOS/blob/master/toolkit/workspace/precompiled/modules/LM_rgb.mpy"
                     pacman install "github.com/BxNxM/micrOS/blob/master/toolkit/workspace/precompiled/modules/LM_rgb.mpy"
      3. GitHub packages (folders via tree/blob URLs or github: form)
            Example: pacman install "github:peterhinch/micropython-mqtt"
                     pacman install "https://github.com/peterhinch/micropython-mqtt/tree/master"
                     pacman install "https://github.com/peterhinch/micropython-mqtt/blob/master/package.json"
                     pacman install "https://github.com/peterhinch/micropython-mqtt"
                     [NOK] pacman install "https://github.com/basanovase/sim7600/tree/main/sim7600" -> Package not found: github:basanovase/sim7600/package.json
      4. Install from local /config/requirements.txt file
            Example: pacman install "requirements.txt"
    """
    from Pacman import install as pm_install
    return pm_install(ref)


def uninstall(name=None):
    """
    Delete package by name from /lib
    :param name: None (default) show installed package name
                 OR package name to delete (str)
    """
    if name is None:
        return list_fs(path=OSPath.LIB, type_filter='d')
    from Pacman import uninstall as pm_uninstall
    return pm_uninstall(name)


def del_duplicates(migrate=True):
    """
    Load module package manager (Not just load modules)
    - delete duplicated .mpy and .py resources, keep .mpy resource!
    """
    modules_path = OSPath.MODULES
    msg_buf = []
    files =  list_fs(path=modules_path, type_filter='f', select='LM')
    py = list((res.split('.')[0] for res in files if res.endswith('.py')))       # Normally smaller list
    mpy = (res.split('.')[0] for res in files if res.endswith('.mpy'))
    for m in mpy:
        # Iterate over mpy resources
        state = True
        if m in py and m != 'main':
            to_delete = f'{m}.py'
            try:
                verdict = remove_file(path_join(modules_path, to_delete))
            except:
                verdict = "n/a"
                state = False
            msg_buf.append(f'   Delete {to_delete} {state} - {verdict}')


    # MIGRATE /ROOT/LMs & IOs -> /modules
    def _migrate_from_root(_rf):
        nonlocal _deleted, files
        if _rf in files:
            remove_file(path_join(OSPath._ROOT, _rf))
            if _rf in ("LM_pacman.mpy", "LM_system.mpy"):
                # Delete protected LMs from root
                remove(path_join(OSPath._ROOT, _rf))
            _deleted += 1
        else:
            rename(path_join(OSPath._ROOT, _rf), path_join(modules_path, _rf))
            msg_buf.append(f'   Move /{_rf} -> modules/{_rf}')
    if migrate:
        from uos import rename, remove
        _deleted = 0
        files = files + list_fs(path=OSPath._ROOT, type_filter='f', select='IO')
        for rf in ilist_fs(path=OSPath._ROOT, type_filter='f', select='LM'):
            _migrate_from_root(rf)
        for rf in ilist_fs(path=OSPath._ROOT, type_filter='f', select='IO'):
            _migrate_from_root(rf)
        if _deleted > 0:
            msg_buf.append(f'   Purged (/): {_deleted}')

    return '\n'.join(msg_buf) if len(msg_buf) > 0 else 'Nothing to delete.'


def moduls(unload=None):
    """
    List / unload loaded upython Load Modules
    :param unload: module name to unload
    :param unload: None - list active modules
    :return str: verdict
    """
    if unload is None:
        return list(modules.keys())
    if unload in modules.keys():
        del modules[unload]
        return f"Module unload {unload} done."
    return f"Module unload {unload} failed."


@socket_stream
def cachedump(delete=None, msgobj=None):
    """
    Cache system persistent data storage files (.cache)
    :param delete: cache name to delete
    """
    data_dir = OSPath.DATA
    if delete is None:
        # List cache files aka application cache
        msg_buf = []
        for cache in (c for c in ilist_fs(data_dir, type_filter='f') if c.endswith('.cache')):
            _path = path_join(data_dir, cache)
            with open(_path, 'r') as f:
                if msgobj is None:
                    msg_buf.append(f'{_path}: {f.read()}')
                else:
                    msgobj(f'{_path}: {f.read()}')
        return msg_buf if len(msg_buf) > 0 else ''
    # Remove given cache file
    try:
        delete_cache = path_join(data_dir, f"{delete}.cache")
        verdict = remove_file(delete_cache)
        return f'{delete_cache} delete done.: {verdict}'
    except:
        return f'{delete}.cache not exists'


def datdump():
    """
    Generic .dat file dump
    - logged data from LMs, sensor data, etc...
    """
    data_dir = OSPath.DATA
    dats = (f for f in ilist_fs(data_dir, type_filter='f') if f.endswith('.dat'))
    out = {}
    for dat in dats:
        with open(path_join(data_dir, dat), 'r') as f:
            out[dat] = f.read()
    return out


def makedir(path):
    """
    Create directory command
    """
    from uos import mkdir
    try:
        mkdir(path)
        return f"{path} dir created."
    except Exception as e:
        return f"{path} failed to create: {e}"

#############################################
#              Legacy features              #
#############################################


@socket_stream
def listmods(msgobj=None):
    """
    Load module package manager
    - list all load modules
    """
    # Dump available LMs
    msg_buf = []
    for k in (res.replace('LM_', '') for res in ilist_fs(path=OSPath.MODULES, type_filter='f', select='LM')):
        if msgobj is None:
            msg_buf.append(f'   {k}')
        else:
            msgobj(f'   {k}')
    return msg_buf if len(msg_buf) > 0 else ''


def delmod(mod):
    """
    Module package manager
    :param mod:
        Delete Load Module with full name: module.py or module.mpy
        OR delete any web resource: *.js, *.css, *.html
    """
    if mod.endswith('py'):
        to_remove = f'LM_{mod}'
    else:
        return f'Invalid {mod}, must ends with .py or .mpy'
    try:
        return remove_file(path_join(OSPath.MODULES, to_remove))
    except Exception as e:
        return f'Cannot delete: {mod}: {e}'


@socket_stream
def micros_checksum(msgobj=None):
    from hashlib import sha1
    from binascii import hexlify
    from Config import cfgget

    for f_name in ilist_fs(path=OSPath.MODULES, type_filter='f', select='LM'):
        with open(f_name, 'rb') as f:
            cs = hexlify(sha1(f.read()).digest()).decode('utf-8')
        msgobj(f"{cs} {f_name}")
    # GC collect?
    return f"micrOS version: {cfgget('version')}"


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return ('listmods', 'delmod mod=<module>.py/.mpy', 'del_duplicates',
            'moduls unload="LM_rgb/None"',
            'cachedump delete=None',
            'datdump',
            'install url="BxNxM/micrOS/master/toolkit/workspace/precompiled/LM_robustness.py"',
            'uninstall name=None',
            'micros_checksum',
            'ls path="/" content="*/f/d" select="*/LM/IO"',
            'rm <path>',
            'rmdir <path>',
            'dirtree path="/"',
            'makedir <path>')
