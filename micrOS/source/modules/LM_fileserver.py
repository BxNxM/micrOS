from json import dumps
from re import compile
from uos import listdir, stat, rename, mkdir

from Common import web_endpoint, web_dir
from Files import path_join, is_dir, remove_dir, remove_file


class Data:
    ROOT_DIR = web_dir("user_data")         # Default Public WEB dir
    TMP_DIR = path_join(ROOT_DIR, "tmp")    # Temporary directory for partial uploads
    UPLOAD_COUNTER = 0                      # Counter for handling partial uploads


def validate_filename(filename: str):
    """
    Check if the provided filename contains only
    alphanumeric characters (including safe symbols).
    """
    filename_pattern = compile(r"^[a-zA-Z0-9._-]+$")
    if not filename_pattern.match(filename):
        raise ValueError("Filename contains invalid characters")


def _list_file_paths_clb():
    user_data = []

    for name in listdir(Data.ROOT_DIR):
        file_path = path_join(Data.ROOT_DIR, name)
        if file_path != Data.TMP_DIR:
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

    if file_to_delete not in listdir(Data.ROOT_DIR):
        raise ValueError(f'File does not exist: {file_to_delete}')
    remove_file(path_join(Data.ROOT_DIR, file_to_delete))
    return 'text/plain', 'ok'


def _upload_file_clb(part_headers: dict, part_body: bytes, first=False, last=False):
    """
    Callback function for handling file uploads (Content-Type: multipart/form-data)
    This callback is invoked on every part.
    """
    cd = part_headers.get('content-disposition', '')
    filename = None
    cd_pattern = compile(r'filename\*?=(?:"([^"]+)"|([^;]+))')

    if match := cd_pattern.search(cd):
        filename = match.group(1) or match.group(2)
        filename = filename.strip()
        # Reject UTF-8 and percent-encoded UTF-8 filenames (RFC 8187)
        if filename.lower().startswith("utf-8'"):
            raise ValueError("Percent encoded filenames are not supported")
        validate_filename(filename)

    if not filename:
        raise ValueError("No valid filename found in part headers")

    if first:
        Data.UPLOAD_COUNTER += 1

    if first and last:
        file_path = path_join(Data.ROOT_DIR, filename)
        with open(file_path, 'wb') as f:
            f.write(part_body)
    elif first and not last:
        file_path = path_join(Data.TMP_DIR, f"{filename}.{Data.UPLOAD_COUNTER}")
        with open(file_path, 'wb') as f:
            f.write(part_body)
    else:
        file_path = path_join(Data.TMP_DIR, f"{filename}.{Data.UPLOAD_COUNTER}")
        with open(file_path, 'ab') as f:
            f.write(part_body)
        if last:
            rename(file_path, path_join(Data.ROOT_DIR, filename))

    return 'text/plain', 'ok'

    
def load(web_data_dir:str=None):
    """
    Initialize fileserver.
    :param web_data_dir: web data public directory (default: web_data)
    """
    if isinstance(web_data_dir, str):
        # Customize public web dir name
        Data.ROOT_DIR = web_dir(web_data_dir)
        Data.TMP_DIR = path_join(Data.ROOT_DIR, 'tmp')
    if is_dir(Data.TMP_DIR):
        remove_dir(Data.TMP_DIR, force=True) # Clean existing partial uploads, is force needed?
    if not is_dir(Data.ROOT_DIR):
        root_dir = web_dir()
        base_dir = root_dir
        for subdir in Data.TMP_DIR.replace(root_dir, "").split('/'):
            current_dir = path_join(base_dir, subdir)
            if not is_dir(current_dir):
                mkdir(current_dir)
            base_dir = current_dir

    # Register endpoints
    web_endpoint('files', _list_file_paths_clb)
    web_endpoint('files', _delete_file_clb, 'DELETE')
    web_endpoint('files', _upload_file_clb, 'POST')
    web_endpoint('files/ui', 'filesui.html')

    return "Fileserver was initialized, endpoints: /files and /files/ui"


#######################
# Helper LM functions #
#######################

def help(widgets=False):
    return (f'load relative_path=<path relative to {web_dir()} for the root directory of user data>',
            'validate_filename "<str>"')
