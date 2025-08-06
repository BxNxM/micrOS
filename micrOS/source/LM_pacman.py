from sys import modules
from Common import socket_stream
from Files import _is_module, list_fs, ilist_fs, remove_fs, OSPath, path_join


#############################################
#     Safe file system handler functions    #
#############################################

def ls(path="/", content='*', raw=False, select='*'):
    """
    Linux like ls command - list app resources and app folders
    :param path: path to list, default: /
    :param content: content type, default all, f-file, d-dir can be selected
    :param raw: keep raw output [(is_app, type), ...]
    :param select: select specific app resource: LM or IO, default: all
    """
    items = list_fs(path, content, select=select)
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


def dirtree(path="/", raw=False):
    """Return only directories from a given path."""
    path = path if path.endswith('/') else f"{path}/"
    folders = [path_join(path, item) for item in ilist_fs(path, type_filter='d')]
    folder_contents = {folder:list_fs(folder) for folder in folders}
    if raw:
        return folder_contents
    formatted_output = ""
    for k, v in folder_contents.items():
        formatted_output += f"{k}\n"
        for val in v:
            formatted_output += f"\t{val[0]}   {val[1]}\n"
    return formatted_output


def download(url=None, package=None):
    """
    [BETA] Load Module downloader with mip
    :param url: github url path, ex. BxNxM/micrOS/master/toolkit/workspace/precompiled/LM_robustness.py
    :param package: mip package name or raw url (hack)
    """
    if url is None and package is None:
        return "Nothing to download, url=None package=None"
    if package is None:
        base_url = "https://raw.githubusercontent.com/"
        file_name = url.split("/")[-1]
        if not(file_name.endswith("py") and file_name.startswith("LM_")):
            return "Invalid file name in url ending, hint: /LM_*.mpy or /LM_*.py"
        # Convert GitHub URL to raw content URL
        if "github.com" in url and "blob" in url:
            url = url.replace("https://github.com/", base_url).replace("/blob", "")
        else:
            url = f"{base_url}{url}"
    else:
        url = package
    from mip import install
    verdict = ""
    try:
        verdict += f"Install {url}\n"
        install(url)
        verdict += "\n|- Done"
    except Exception as e:
        verdict += f"|- Cannot install: {url}\n{e}"
    return verdict


def del_duplicates():
    """
    Load module package manager (Not just load modules)
    - delete duplicated .mpy and .py resources, keep .mpy resource!
    """
    msg_buf = []
    files =  list_fs(type_filter='f', select='LM')
    py = list((res.split('.')[0] for res in files if res.endswith('.py')))       # Normally smaller list
    mpy = (res.split('.')[0] for res in files if res.endswith('.mpy'))
    for m in mpy:
        # Iterate over mpy resources
        state = True
        if m in py and m != 'main':
            to_delete = f'{m}.py'
            try:
                verdict = remove_fs(to_delete)
            except:
                verdict = "n/a"
                state = False
            msg_buf.append(f'   Delete {to_delete} {state} - {verdict}')
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
    for k in (res.replace('LM_', '') for res in ilist_fs(type_filter='f', select='LM')):
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
    if mod.endswith('py') or _is_module(mod):
        try:
            to_remove = f'LM_{mod}' if mod.endswith('py') else mod
            return remove_fs(to_remove)
        except Exception as e:
            return f'Cannot delete: {mod}: {e}'
    return f'Invalid value: {mod}'


@socket_stream
def micros_checksum(msgobj=None):
    from hashlib import sha1
    from binascii import hexlify
    from Config import cfgget

    for f_name in ilist_fs(type_filter='f', select='LM'):
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
    return ('listmods', 'delmod mod=<module>.py/.mpy or .js/.html/.css', 'del_duplicates',
            'moduls unload="LM_rgb/None"',
            'cachedump delete=None',
            'datdump',
            'download url="BxNxM/micrOS/master/toolkit/workspace/precompiled/LM_robustness.py"',
            'micros_checksum',
            'ls path="/" content="*/f/d" select="*/LM/IO"',
            'rm <path>',
            'dirtree path="/"',
            'makedir <path>')
