from os import listdir, remove
from sys import modules
from Common import socket_stream

WEB_EXT = ('html', 'js', 'css')

@socket_stream
def listmods(msgobj=None):
    """
    Load module package manager
    - list all load modules
    """
    # Dump available LMs
    msg_buf = []
    for k in (res.replace('LM_', '') for res in listdir()
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
        # LM exception list - system and lmpacman cannot be deleted
        if 'lmpacman.' in mod or 'system.' in mod:
            return f'Load module {mod} is in use, skip delete.'
        try:
            to_remove = mod if mod.split('.')[-1] in WEB_EXT else f'LM_{mod}'
            remove(to_remove)
            return f'Delete module: {mod}'
        except Exception as e:
            return f'Cannot delete: {mod}: {e}'
    return f'Invalid value: {mod}'


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


def module(unload=None):
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
def cachedump(cdel=None, msgobj=None):
    """
    Cache system persistent data storage files (.pds)
    """
    if cdel is None:
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
        remove(f'{cdel}.pds')
        return f'{cdel}.pds delete done.'
    except:
        return f'{cdel}.pds not exists'


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
    return 'listmods', 'delmod mod=<module>.py/.mpy or .js/.html/.css', 'del_duplicates',\
           'module unload="LM_rgb/None"',\
           'cachedump cdel="rgb.pds/None"', 'micros_checksum'
