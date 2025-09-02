from sys import modules
from Common import socket_stream
from Files import is_protected, list_fs, ilist_fs, remove_fs, OSPath, path_join


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


def rm(path, allow_dir=False):
    """
    Linux like rm command - delete app resources and folders
    :param path: app resource name/path, ex.: LM_robustness.py
    :param allow_dir: enable directory deletion, default: False
    """
    return remove_fs(path, allow_dir)


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


def download(url=None, package=None):
    """
    [BETA] Load Module downloader with mip
    :param url: github url path, ex. BxNxM/micrOS/master/toolkit/workspace/precompiled/LM_robustness.py
    :param package: mip package name or raw url (hack)
    """
    def _install(target=None):
        nonlocal url, verdict
        try:
            verdict += f"Install {url}\n"
            if target is None:
                install(url)                    # Default download: /lib
            else:
                install(url, target=target)     # Custom target
            verdict += "\n|- Done"
        except Exception as e:
            verdict += f"|- Cannot install: {url}\n{e}"
        return verdict

    from mip import install
    verdict = ""
    if url is None and package is None:
        return "Nothing to download, url=None package=None"
    if package is None:
        verdict += "Install from GitHub URL"
        base_url = "https://raw.githubusercontent.com/"
        file_name = url.split("/")[-1]
        if not(file_name.endswith("py") and file_name.startswith("LM_")):
            return "Invalid file name in url ending, hint: /LM_*.mpy or /LM_*.py"
        # Convert GitHub URL to raw content URL
        if "github.com" in url and "blob" in url:
            url = url.replace("https://github.com/", base_url).replace("/blob", "")
        else:
            url = f"{base_url}{url}"
        return _install(target=OSPath.MODULES)          # Install module from Github URL
    url = package
    return _install()                                   # Install official package


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
                verdict = remove_fs(path_join(modules_path, to_delete))
            except:
                verdict = "n/a"
                state = False
            msg_buf.append(f'   Delete {to_delete} {state} - {verdict}')


    # MIGRATE /ROOT/LMs & IOs -> /modules
    def _migrate_from_root(_rf):
        nonlocal _deleted, files
        if _rf in files:
            remove_fs(path_join(OSPath._ROOT, _rf))
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
        verdict = remove_fs(delete_cache)
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
        return remove_fs(path_join(OSPath.MODULES, to_remove))
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
            'download url="BxNxM/micrOS/master/toolkit/workspace/precompiled/LM_robustness.py"',
            'micros_checksum',
            'ls path="/" content="*/f/d" select="*/LM/IO"',
            'rm <path>',
            'dirtree path="/"',
            'makedir <path>')
