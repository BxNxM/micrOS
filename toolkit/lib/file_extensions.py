

ENABLED_EXTENSIONS = ('py', 'mpy', 'js', 'css', 'html')
WEB_ONLY = ('js', 'html', 'css')

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