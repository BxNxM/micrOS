"""
micrOS Fileserver addon for WebEngine
"""

from json import dumps
from re import compile as recompile
from uos import listdir, stat, rename, mkdir, statvfs

from Common import web_endpoint, web_mounts, web_dir
from Files import path_join, is_dir, remove_dir, remove_file, OSPath
from Web import WebEngine


class Shared:
    ROOT_DIR = web_dir("user_data")         # Default Public WEB dir
    TMP_DIR = path_join(ROOT_DIR, "tmp")    # Temporary directory for partial uploads
    UPLOAD_COUNTER = 0                      # Counter for handling partial uploads

    @staticmethod
    def normalize_input_path(filename):
        # Hack the file name to accept folder prefix if allowed dir... (user_data)
        user_dir_name = Shared.ROOT_DIR.split("/")[-1]
        filename = filename.lstrip("/")  # normalize
        if filename.startswith(user_dir_name):
            filename = filename.replace(f"{user_dir_name}/", "")
        return filename, user_dir_name


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

    user_data = []
    # Resolve mount aliases
    err, root_dir = WebEngine.url_path_resolve(root_dir.replace(web_dir(), ""))
    if err:
        return "text/plain", root_dir

    # Show file content on selected root_dir
    for name in listdir(root_dir):
        if name.endswith(".mpy"):
            # Skip .mpy files, not editable
            continue
        file_path = path_join(root_dir, name)
        if file_path != Shared.TMP_DIR:
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
    validate_filename(file_to_delete)

    # Resolve mount aliases
    err, root_dir = WebEngine.url_path_resolve(file_to_delete.replace(web_dir(), ""))
    if err:
        return "text/plain", root_dir

    if file_to_delete not in listdir(Shared.ROOT_DIR):
        raise ValueError(f'File does not exist: {file_to_delete}')
    remove_file(path_join(Shared.ROOT_DIR, file_to_delete))
    return 'text/plain', 'ok'


def _upload_file_clb(part_headers: dict, part_body: bytes, first=False, last=False):
    """
    Callback function for handling file uploads (Content-Type: multipart/form-data)
    This callback is invoked on every part.
    """
    cd = part_headers.get('content-disposition', '')
    filename = None
    cd_pattern = recompile(r'filename\*?=(?:"([^"]+)"|([^;]+))')

    if match := cd_pattern.search(cd):
        filename = match.group(1) or match.group(2)
        filename = filename.strip()
        # Reject UTF-8 and percent-encoded UTF-8 filenames (RFC 8187)
        if filename.lower().startswith("utf-8'"):
            raise ValueError("Percent encoded filenames are not supported")
        filename, _ = Shared.normalize_input_path(filename)
        validate_filename(filename)

    if not filename:
        raise ValueError("No valid filename found in part headers")

    if first:
        Shared.UPLOAD_COUNTER += 1

    if first and last:
        file_path = path_join(Shared.ROOT_DIR, filename)
        with open(file_path, 'wb') as f:
            f.write(part_body)
    elif first and not last:
        file_path = path_join(Shared.TMP_DIR, f"{filename}.{Shared.UPLOAD_COUNTER}")
        with open(file_path, 'wb') as f:
            f.write(part_body)
    else:
        file_path = path_join(Shared.TMP_DIR, f"{filename}.{Shared.UPLOAD_COUNTER}")
        with open(file_path, 'ab') as f:
            f.write(part_body)
        if last:
            rename(file_path, path_join(Shared.ROOT_DIR, filename))

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
    web_endpoint('fs/files', _list_file_paths_clb)          # OBSOLETE: GET body send browser restriction rule
    web_endpoint('fs/list', _list_file_paths_clb, 'POST')
    web_endpoint('fs/list', lambda: ('text/plain', 'USE THIS AS POST Endpoint, to list selected dir files over http body'))
    web_endpoint('fs/files', _delete_file_clb, 'DELETE')
    web_endpoint('fs/files', _upload_file_clb, 'POST')
    web_endpoint('fs/dirs', lambda: ('application/json', dumps(get_shared_dirs())))
    web_endpoint('fs/usage', _disk_usage_clb)
    web_endpoint('fs', 'filesui.html')

    return "Fileserver was initialized, endpoints: /fs, /fs/files, /fs/dirs, /fs/usage"


def validate_filename(filename: str):
    """
    Check if the provided filename contains only
    alphanumeric characters (including safe symbols).
    """
    filename, dirname = Shared.normalize_input_path(filename)
    # Real check
    filename_pattern = recompile(r"^[a-zA-Z0-9._-]+$")
    if not filename_pattern.match(filename):
        raise ValueError(f"Filename contains invalid characters: {filename} ({dirname})")


def get_shared_dirs() -> list:
    """
    Getter for web shared dirs
    - default: /web/Shared.ROOT_DIR
    - extended: web_mounts()
    """
    web_dirs = list([a for a, p in web_mounts().items() if p is not None])
    web_dirs.insert(0, Shared.ROOT_DIR.replace(web_dir(), ""))
    return web_dirs


def extend_mounts(modules:bool=None, data:bool=None):
    """
    Extend web engine shared root path list
    :param modules: add /modules to web shared path
    :param data: add /data to web shared path
    """
    return web_mounts(modules, data)

#######################
# Helper LM functions #
#######################

def help(widgets=False):
    return (f'load web_data_dir=<shared directory under {web_dir()}>',
            'validate_filename "<str>"',
            'get_shared_dirs',
            'extend_mounts modules:bool=None data:bool=None')
