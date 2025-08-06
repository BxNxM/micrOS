import os

try:
    from .lib import LocalMachine
    from .lib.file_extensions import check_all_extensions, check_web_extensions
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    from lib import LocalMachine
    from lib.file_extensions import check_all_extensions, check_web_extensions

def micros_resource_list(root_folder):
    resources_path = []
    subfolders = []
    for source in LocalMachine.FileHandler.list_dir(root_folder):
        source_full_path = os.path.join(root_folder, source)
        # [1] / Root directory source files and folders.
        if check_all_extensions(source):
            resources_path.append(source_full_path)
        # [2] /dir Handle sub dictionary sources
        elif LocalMachine.FileHandler.path_is_exists(source_full_path)[1] == 'd':
            subfolders.append(source)
            for sub_source in LocalMachine.FileHandler.list_dir(source_full_path):
                sub_source_full_path = os.path.join(source_full_path, sub_source)
                if check_all_extensions(sub_source):
                    resources_path.append(sub_source_full_path)
    return resources_path, subfolders
