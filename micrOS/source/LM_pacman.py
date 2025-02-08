from uos import listdir, remove, stat
from sys import modules
from Common import socket_stream

WEB_EXT = ('html', 'js', 'css')
DATA_TYPES = ('log', 'pds', 'dat')

def _is_app_resource(path='/'):
    if stat(path)[0] & 0x4000:      # Dir check
        return True, 'd'
    file_name = path.split("/")[-1]
    if file_name.startswith('LM_') or file_name.split('.')[-1] in WEB_EXT + DATA_TYPES:
        return True, 'f'
    return False, '?'


#############################################
#     Safe file system handler functions    #
#############################################

def ls(path="/", content='*', raw=False):
    """
    Linux like ls command - list app resources and app folders
    :param path: path to list, default: /
    :param content: content type, default all, f-file, d-dir can be selected
    :param raw: keep raw output [(is_app, type), ...]
    """
    path = path if path.endswith('/') else f"{path}/"
    items = []
    for item in listdir(path):
        is_app, item_type = _is_app_resource(path + item)
        if is_app and (content == "*" or item_type == content):
            items.append((item_type, item))
    if raw:
        return items
    formatted_output = ""
    i = 0
    for f in items:
        i += 1
        spacer = " " * (4 - len(str(i)))
        formatted_output += f"{i}{spacer}{f[0]}   {f[1]}\n"
    return formatted_output


def rm(path):
    """
    Linux like rm command - delete app resources and folders
    :param path: app resource name/path, ex.: LM_robustness.py
    """
    if 'pacman.' in path or 'system.' in path or "/" == path.strip():
        return f'Load module {path} is protected, skip delete.'
    is_app, item_type = _is_app_resource(path)
    if is_app:
        remove(path)
        return f"Remove: {path} {'dir' if item_type == 'd' else 'file'}"
    return f"Invalid path {path}"


def dirtree(path="/", raw=False):
    """Return only directories from a given path."""
    path = path if path.endswith('/') else f"{path}/"
    folders = [f"{path}/{item}" for item in listdir(path) if _is_app_resource(f"{path}{item}")[1] == 'd']
    folder_contents = {folder:listdir(folder) for folder in folders}
    if raw:
        return folder_contents
    formatted_output = ""
    for k, v in folder_contents.items():
        formatted_output += f"{k}\n"
        for val in v:
            formatted_output += f"\t{val}\n"
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
    py = list((res.split('.')[0] for res in listdir() if res.endswith('.py')))       # Normally smaller list
    mpy = (res.split('.')[0] for res in listdir() if res.endswith('.mpy'))
    for m in mpy:
        # Iterate over mpy resources
        state = True
        if m in py and m != 'main':
            to_delete = f'{m}.py'
            try:
                remove(to_delete)
            except:
                state = False
            msg_buf.append(f'   Delete {to_delete} {state}')
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
def cachedump(delpds=None, msgobj=None):
    """
    Cache system persistent data storage files (.pds)
    :param delpds: cache name to delete
    """
    if delpds is None:
        # List pds files aka application cache
        msg_buf = []
        for pds in (_pds for _pds in listdir() if _pds.endswith('.pds')):
            with open(pds, 'r') as f:
                if msgobj is None:
                    msg_buf.append(f'{pds}: {f.read()}')
                else:
                    msgobj(f'{pds}: {f.read()}')
        return msg_buf if len(msg_buf) > 0 else ''
    # Remove given pds file
    try:
        remove(f'{delpds}.pds')
        return f'{delpds}.pds delete done.'
    except:
        return f'{delpds}.pds not exists'


def dat_dump():
    """
    Generic .dat file dump
    - logged data from LMs, sensor datat, etc...
    """
    logs_dir = "/logs/"
    dats = (f for f in listdir(logs_dir) if f.endswith('.dat'))
    out = {}
    for dat in dats:
        with open(f"{logs_dir}{dat}", 'r') as f:
            out[dat] = f.read()
    return out

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
    for k in (res.replace('LM_', '') for res in listdir("/")
              if res.startswith('LM_') or res.split('.')[-1] in WEB_EXT):
        if msgobj is None:
            msg_buf.append(f'   {k}')
        else:
            msgobj(f'   {k}')
    return msg_buf if len(msg_buf) > 0 else ''


def delmod(mod=None):
    """
    Module package manager
    :param mod:
        Delete Load Module with full name: module.py or module.mpy
        OR delete any web resource: *.js, *.css, *.html
    """
    if mod is not None and (mod.endswith('py') or mod.split('.')[-1] in WEB_EXT):
        # LM exception list - system and pacman cannot be deleted
        if 'pacman.' in mod or 'system.' in mod:
            return f'Load module {mod} is in use, skip delete.'
        try:
            to_remove = mod if mod.split('.')[-1] in WEB_EXT else f'LM_{mod}'
            remove(to_remove)
            return f'Delete module: {mod}'
        except Exception as e:
            return f'Cannot delete: {mod}: {e}'
    return f'Invalid value: {mod}'


@socket_stream
def micros_checksum(msgobj=None):
    from hashlib import sha1
    from binascii import hexlify
    from Config import cfgget

    for f_name in (_pds for _pds in listdir() if _pds.endswith('py')):
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
            'cachedump delpds="rgb/None"',
            'dat_dump',
            'download url="BxNxM/micrOS/master/toolkit/workspace/precompiled/LM_robustness.py"',
            'micros_checksum',
            'ls path="/" content="*/f/d"',
            'rm <path>', 'dirtree path="/"')
