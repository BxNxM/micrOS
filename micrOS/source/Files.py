from uos import ilistdir, remove, stat, getcwd

################################   Helper functions   #####################################

def _is_module(path:str='/', pyprefix:str='*') -> bool:
    """
    Filter application modules, LM_.* (pyprefix) or app data or web resource
    :param path: file to check
    :param pyprefix: python resource filter prefix, default: * (all: LM and IO)
    """
    # micrOS file types
    allowed_exts = ('html', 'js', 'css', 'log', 'cache', 'dat')
    mod_prefixes = ('LM', "IO")
    fname = path.split("/")[-1]
    if fname.split("_")[0] in mod_prefixes or fname.split('.')[-1] in allowed_exts:
        if pyprefix == '*':
            # MODE: ALL app resources
            return True
        if fname.startswith(f"{pyprefix.upper()}_"):
            # MODE: SELECTED app resources
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
            if not core and item_type == 'f' and not _is_module(path+item, pyprefix=select):
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
    if 'pacman.mpy' in path or 'system.mpy' in path or "/" == path.strip():
        return f'Load module {path} is protected, skip deletion'
    _is_dir = is_dir(path)
    if _is_module(path) or (_is_dir and allow_dir):
        remove(path)
        return f"Removed: {path} {'dir' if _is_dir else 'file'}"
    return f"Protected path: {path}"


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


def path_join(*parts):
    path = "/".join(part.strip("/") for part in parts if part)
    if parts and parts[0].startswith("/"):
        path = "/" + path
    return path


# micrOS system file structure
class OSPath:
    _ROOT = getcwd()
    LOGS = path_join(_ROOT, '/logs')        # Logs (.log)
    DATA = path_join(_ROOT,'/data')         # Application data (.dat, .cache, etc.)
    WEB = path_join(_ROOT,'/web')           # Web resources (.html, .css, .js, .json, etc.)
    MODULES = path_join(_ROOT, '/modules')  # Application modules (.mpy, .py) (todo)
    CONFIG = path_join(_ROOT, '/config')    # System configuration files (node_config.json, etc.)(todo)

    @property
    def ROOT(self):
        return self._ROOT
