import sys
import json
import os
from re import compile

from Common import web_endpoint, web_dir
from Files import path_join, is_dir, remove_dir


class Data:
    ROOT_DIR = ''
    TMP_DIR = ''        # Temporary directory for partial uploads
    UPLOAD_COUNTER = 0  # Counter for handling partial uploads


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

    for name in os.listdir(Data.ROOT_DIR):
        file_path = path_join(Data.ROOT_DIR, name)
        if file_path != Data.TMP_DIR:
            user_data.append(file_path)

    response = [
        {
            'path': file_path.replace(web_dir(),""),
            'size': os.stat(file_path)[6],
            'created': os.stat(file_path)[9]
        }
        for file_path in user_data
    ]
    return 'application/json', json.dumps(response)


def _delete_file_clb(file_to_delete: bytes):
    file_to_delete = file_to_delete.decode('ascii')
    validate_filename(file_to_delete)

    if file_to_delete not in os.listdir(Data.ROOT_DIR):
        raise ValueError(f'File does not exist: {file_to_delete}')
    os.remove(path_join(Data.ROOT_DIR, file_to_delete))
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
            os.rename(file_path, path_join(Data.ROOT_DIR, filename))

    return 'text/plain', 'ok'

    
def load(relative_path='user_data'):
    """
    Initialize fileserver.
    :param relative_path str: relative path for the root directory of user data
    """
    Data.ROOT_DIR = web_dir(relative_path)
    if not is_dir(Data.ROOT_DIR):
        base_dir = '/'
        for subdir in Data.ROOT_DIR.split('/'):
            current_dir = path_join(base_dir,subdir)
            if not is_dir(current_dir):
                os.mkdir(current_dir)
            base_dir = current_dir

    Data.TMP_DIR = path_join(Data.ROOT_DIR, 'tmp')
    if is_dir(Data.TMP_DIR):
        remove_dir(Data.TMP_DIR, force=True) # Clean existing partial uploads
    os.mkdir(Data.TMP_DIR)

    web_endpoint('files', _list_file_paths_clb)
    web_endpoint('files', _delete_file_clb, 'DELETE')
    web_endpoint('files', _upload_file_clb, 'POST')


#######################
# Helper LM functions #
#######################

def help(widgets=False):
    return f'load relative_path=<path relative to {web_dir()} for the root directory of user data>',
