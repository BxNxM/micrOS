"""
micrOS Fileserver addon for WebEngine
"""

from json import dumps
from re import compile as recompile
from uos import stat, rename, mkdir, statvfs

from Common import web_endpoint, web_mounts, web_dir, syslog
from Files import path_join, is_dir, remove_dir, remove_file, OSPath, abs_path, ilist_fs
from Web import url_path_resolve


class Shared:
    ROOT_DIR = web_dir("user_data")         # Default Public WEB dir
    TMP_DIR = path_join(ROOT_DIR, "tmp")    # Temporary directory for partial uploads
    UPLOAD_COUNTER = 0                      # Counter for handling partial uploads
    MOUNTS_WRITE_ACCESS = {"$modules": False, "$data": False, "$logs": False}
    # mpy: code bytestream
    HIDE_FEXT = ("mpy",)                    # Hide / Protect (delete/upload) files with the listed extensions

    @staticmethod
    def check_write_access(path):
        """
        Raw input path mount write access checker
        """
        if "$" in path:
            # Mount alias in path
            for access in Shared.MOUNTS_WRITE_ACCESS:
                if access in path:
                    if Shared.MOUNTS_WRITE_ACCESS[access]:
                        return      # Writeable
                    raise ValueError(f'ReadOnly path: {path}')
        else:
            # No mount alias in path
            return      # Writeable
        raise ValueError(f'ReadOnly path: {path}')


#############################################
#           Web Endpoint Callbacks          #
#############################################

def _list_file_paths_clb(root_dir=None):
    """
    List files shared path
    """
    if isinstance(root_dir, bytes)and len(root_dir.strip()) > 0:
        # Decode input path from request body
        root_dir = root_dir.decode("ascii")
    else:
        root_dir = Shared.ROOT_DIR

    # Resolve and Validate path (mount aliases)
    try:
        root_dir = resolve_path(root_dir.replace(web_dir(), ""))
    except Exception as e:
        return "text/plain", str(e)

    user_data = []
    # Show file content on selected root_dir
    # Hide: .mpy files (non-readable/non-editable)
    for name in (f for f in ilist_fs(path=root_dir, type_filter='f') if f.split(".")[-1] not in Shared.HIDE_FEXT):
        file_path = path_join(root_dir, name)
        user_data.append(file_path)

    response = [
        {
            'path': file_path.replace(web_dir(),""),
            'size': stat(file_path)[6],
            'created': stat(file_path)[9]
        }
        for file_path in user_data
    ]
    return 'application/json', dumps(response)


def _delete_file_clb(file_to_delete: bytes):
    file_to_delete = file_to_delete.decode('ascii')
    Shared.check_write_access(file_to_delete)
    filepath = resolve_path(file_to_delete)
    if is_dir(filepath):
        raise ValueError(f'File does not exist: {filepath}')
    # File name extension based delete protection
    if filepath.split(".")[-1] in Shared.HIDE_FEXT:
        raise ValueError(f'Delete access denied: {filepath}')
    verdict = remove_file(filepath)
    return 'text/plain', verdict


def _upload_file_clb(part_headers: dict, part_body: bytes, first=False, last=False):
    """
    Callback function for handling file uploads (Content-Type: multipart/form-data)
    This callback is invoked on every part.
    """
    cd = part_headers.get('content-disposition', '')
    target_filepath = None
    filename = ""
    cd_pattern = recompile(r'filename\*?=(?:"([^"]+)"|([^;]+))')

    if match := cd_pattern.search(cd):
        filepath = match.group(1) or match.group(2)
        filepath = filepath.strip()
        # Reject UTF-8 and percent-encoded UTF-8 filenames (RFC 8187)
        if filepath.lower().startswith("utf-8'"):
            raise ValueError("Percent encoded filenames are not supported")
        Shared.check_write_access(filepath)
        target_filepath = resolve_path(filepath)
        filename = target_filepath.split("/")[-1]

    # File name extension based upload protection
    if not filename or filename.split(".")[-1] in Shared.HIDE_FEXT:
        raise ValueError(f"Invalid filename in part headers: {filename}")
    target_parts = target_filepath.strip("/").split("/")
    if len(target_parts) == 2 and target_parts[-2] == "web":
        # Write protected /web root -> redirect to user shared dir
        target_filepath = path_join(Shared.ROOT_DIR, filename)

    if first:
        Shared.UPLOAD_COUNTER += 1

    if first and last:
        with open(target_filepath, 'wb') as f:
            f.write(part_body)
    elif first and not last:
        tmp_file_path = path_join(Shared.TMP_DIR, f"{filename}.{Shared.UPLOAD_COUNTER}")
        with open(tmp_file_path, 'wb') as f:
            f.write(part_body)
    else:
        tmp_file_path = path_join(Shared.TMP_DIR, f"{filename}.{Shared.UPLOAD_COUNTER}")
        with open(tmp_file_path, 'ab') as f:
            f.write(part_body)
        if last:
            rename(tmp_file_path, target_filepath)

    return 'text/plain', 'ok'


def _disk_usage_clb():
    """
    Calculate disk usage
    return {'used': <bytes used>, 'free': <bytes free>}
    """
    # Check root dir usage
    fs_stat = statvfs(OSPath._ROOT)
    fs_free = fs_stat[0] * fs_stat[3]
    fs_size = fs_stat[0] * fs_stat[2]
    used = fs_size - fs_free
    return 'application/json', dumps({'used': used, 'free': fs_free})


#############################################
#              Public functions             #
#############################################

def load(web_data_dir:str=None):
    """
    Initialize fileserver.
    :param web_data_dir: web data public directory (default: /web/<user_data>)
    """
    if isinstance(web_data_dir, str):
        # Customize public web dir name
        Shared.ROOT_DIR = web_dir(web_data_dir)
        Shared.TMP_DIR = path_join(Shared.ROOT_DIR, 'tmp')
    if is_dir(Shared.TMP_DIR):
        remove_dir(Shared.TMP_DIR, force=True) # Clean existing partial uploads, is force needed?
    if not is_dir(Shared.ROOT_DIR):
        root_dir = web_dir()
        base_dir = root_dir
        for subdir in Shared.TMP_DIR.replace(root_dir, "").split('/'):
            current_dir = path_join(base_dir, subdir)
            if not is_dir(current_dir):
                mkdir(current_dir)
            base_dir = current_dir

    # Register endpoints
    web_endpoint('fs/dirs', lambda: ('application/json', dumps(get_shared_dirs())))
    web_endpoint('fs/list', lambda: ('text/plain', 'USE THIS AS POST Endpoint, select dir in http body'))
    web_endpoint('fs/list', _list_file_paths_clb, 'POST')
    web_endpoint('fs/files', lambda: ('text/plain', "USE THIS AS POST / DELETE Endpoint, select file in http body"))
    web_endpoint('fs/files', _delete_file_clb, 'DELETE')
    web_endpoint('fs/files', _upload_file_clb, 'POST')
    web_endpoint('fs/usage', _disk_usage_clb)
    web_endpoint('fs', 'filesui.html')

    return "Fileserver was initialized, endpoints: /fs, /fs/files, /fs/dirs, /fs/usage"


def resolve_path(path):
    """
    Resolve and Validate input path
    :param path: URL resource path or mount path string
    """
    # Path resolve and validation
    path = abs_path(path)
    err, path = url_path_resolve(path)
    if err:
        raise ValueError(f"Invalid path: {path}")
    filename = path.split("/")[-1]
    # Filename validation
    filename_pattern = recompile(r"^[a-zA-Z0-9._-]+$")
    if not filename_pattern.match(filename):
        raise ValueError(f"Filename contains invalid characters: {path}")
    return path


def get_shared_dirs() -> list:
    """
    Getter for web shared dirs
    - default: /web/Shared.ROOT_DIR
    - extended: web_mounts()
    """
    web_dirs = list([a for a, p in web_mounts().items() if p is not None])
    web_dirs.insert(0, Shared.ROOT_DIR.replace(web_dir(), ""))
    return web_dirs


def get_user_dir():
    """
    Getter for user configured shared dir
    - used by other load modules
    """
    return Shared.ROOT_DIR


def extend_mounts(modules:bool=None, data:bool=None, logs:bool=None):
    """
    Extend web engine shared root path list
    :param modules: add/remove /modules to web shared path
    :param data: add/remove /data to web shared path
    :param logs: add/remove /logs web shared path
    """
    return web_mounts(modules, data, logs)


def mounts_write_access(modules:bool=None, data:bool=None, logs:bool=None):
    if modules is not None:
        Shared.MOUNTS_WRITE_ACCESS["$modules"] = modules
    if data is not None:
        Shared.MOUNTS_WRITE_ACCESS["$data"] = data
    if logs is not None:
        Shared.MOUNTS_WRITE_ACCESS["$logs"] = logs
    return Shared.MOUNTS_WRITE_ACCESS

#######################
# Helper LM functions #
#######################

def help(widgets=False):
    return (f'load web_data_dir=<shared directory under {web_dir()}>',
            'resolve_path "<str>"',
            'get_shared_dirs',
            'get_user_dir',
            'extend_mounts modules:bool=None data:bool=None logs:bool=None',
            'mounts_write_access modules:bool=None data:bool=None logs:bool=None')
