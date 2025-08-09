import os

try:
    from . import LocalMachine
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    import LocalMachine

PYTHON_EXTENSIONS = ('py', 'mpy')
WEB_ONLY = ('js', 'html', 'css', 'json', 'ico', 'jpeg', 'png')
ENABLED_EXTENSIONS = PYTHON_EXTENSIONS + WEB_ONLY

def check_all_extensions(path):
    extension = path.split('.')[-1]
    if extension in ENABLED_EXTENSIONS:
        return True
    return False

def check_web_extensions(path):
    extension = path.split('.')[-1]
    if extension in WEB_ONLY:
        return True
    return False

def check_python_extensions(path):
    extension = path.split('.')[-1]
    if extension in PYTHON_EXTENSIONS:
        return True
    return False

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
