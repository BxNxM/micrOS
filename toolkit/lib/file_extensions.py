
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