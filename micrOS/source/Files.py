"""
Module is responsible high level micropython file system opeartions
[IMPORTANT] This module must never use any micrOS specific functions or classes.
"""

from uos import ilistdir, remove, stat, getcwd, mkdir
from sys import path as upath

################################   Helper functions   #####################################

def _filter(path:str='/', ext:tuple=None, prefix:tuple=None, hide_core:bool=True) -> bool:
    """
    Filter files
    :param path: file to check
    :param ext: tuple of extensions to filter by, default: None (all)
    :param hide_core: hide core files (mpy, py), default: True
    """
    fname = path.split("/")[-1]
    _ext = fname.split(".")[-1]
    if hide_core and _ext in ("mpy", "py") and not (fname.startswith("LM_") or fname.startswith("IO_")):
        return False
    if ext is None and prefix is None:
        return True
    if isinstance(prefix, tuple) and fname.split("_")[0] in prefix:
        return True
    if isinstance(ext, tuple) and fname.split(".")[-1] in ext:
        return True
    return False

def is_protected(path:str='/') -> bool:
    """
    Check is file protected
        - deny deletion
    """
    protected_entities = ("", "node_config.json", "modules", "config", "logs", "web", "data",
                          "LM_pacman.mpy", "LM_system.mpy")
    entity = path.split("/")[-1].replace("/", "")
    if entity in protected_entities:
        return True
    return False

def _type_mask_to_str(item_type:int=None) -> str:
    # Map the raw bit-mask to a single character
    if item_type & 0x4000:              # Dir bit-mask
        item_type = 'd'
    elif item_type & 0x8000:            # File bit-mask
        item_type = 'f'
    else:
        item_type = 'o'
    return item_type

###########################   Public functions   #############################
def is_dir(path):
    try:
        return stat(path)[0] & 0x4000
    except OSError:
        return False


def is_file(path):
    try:
        return stat(path)[0] & 0x8000
    except OSError:
        return False


def ilist_fs(path:str="/", type_filter:str='*', select:str='*', core:bool=False):
    """
    Linux like ls command - list app resources and app folders
    :param path: path to list, default: /
    :param type_filter: content type, default all (*), f-file, d-dir can be selected
    :param select: select specific application resource type by prefix: LM or IO
    :param core: list core files resources as well, default: False
    return iterator:
        when content is all (*) output: [(item_type, item), ...]
        OR
        content type was selected (not *) output: [item, ...]
    """
    path = path if path.endswith('/') else f"{path}/"
    # Info: uos.ilistdir: (name, type, inode[, size])
    for item, item_type, *_ in ilistdir(path):
        item_type = _type_mask_to_str(item_type)
        if type_filter in ("*", item_type):
            # Mods only
            _select = None if select == "*" else (select,)
            if item_type == 'f' and not _filter(item, prefix=_select, hide_core=not core):
                continue
            if select != '*' and item_type == 'd':
                continue
            # Create result
            if type_filter == "*":
                yield item_type, item
            else:
                yield item


def list_fs(path:str="/", type_filter:str='*', select:str='*', core:bool=False) -> list[str,] | list[tuple[str, str],]:
    """
    Wrapper of ilist_fs
    Return list
    """
    return list(ilist_fs(path, type_filter, select, core))


def remove_fs(path, allow_dir=False):
    """
    Linux like rm command - delete app resources and folders
    :param path: app resource path
    :param allow_dir: enable directory deletion, default: False
    """
    # protect some resources
    if is_protected(path):
        return f'{path} is protected, skip deletion'
    _is_file = is_file(path)
    if _is_file or allow_dir:
        remove(path)
        return f"{path} deleted"
    return f"Cannot delete {'file' if _is_file else 'dir'}: {path}"


def path_join(*parts):
    path = "/".join(part.strip("/") for part in parts if part)
    if parts and parts[0].startswith("/"):
        path = path if path.startswith("/") else "/" + path
    return path


# micrOS system file structure
class OSPath:
    _ROOT = getcwd()
    LOGS = path_join(_ROOT, '/logs')        # Logs (.log)
    DATA = path_join(_ROOT,'/data')         # Application data (.dat, .cache, etc.)
    WEB = path_join(_ROOT,'/web')           # Web resources (.html, .css, .js, .json, etc.)
    MODULES = path_join(_ROOT, '/modules')  # Application modules (.mpy, .py)
    CONFIG = path_join(_ROOT, '/config')    # System configuration files (node_config.json, etc.)


def init_micros_dirs():
    """
    Init micrOS root file system directories
    """
    # ENABLE MODULES ACCESS
    if OSPath.MODULES not in upath:
        upath.insert(0, OSPath.MODULES)

    root_dirs = [
        getattr(OSPath, key)
        for key in dir(OSPath)
        if not key.startswith("_") and isinstance(getattr(OSPath, key), str)
    ]
    print(f"[BOOT] rootFS validation: {root_dirs}")
    for dir_path in root_dirs:
        if not is_dir(dir_path):
            try:
                mkdir(dir_path)
                print(f"[BOOT] init dir: {dir_path}")
            except Exception as e:
                print(f"[ERR][BOOT] cannot init dir {dir_path}: {e}")
