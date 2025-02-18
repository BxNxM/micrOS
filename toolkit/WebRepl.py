import sys
import os

MYDIR = os.path.dirname(__file__)
print("Module [WebRepl] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYDIR))
try:
    from .lib.TerminalColors import Colors
    from .lib.LocalMachine import FileHandler, CommandHandler, SimplePopPushd
    from .socketClient import ConnectionData
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    from lib.TerminalColors import Colors
    from lib.LocalMachine import FileHandler, CommandHandler, SimplePopPushd
    from socketClient import ConnectionData

WEBREPL_DIR = os.path.join(MYDIR, "workspace/webrepl")
MAKE_HTML_WEBPAGE_PATH = os.path.join(WEBREPL_DIR, "make_html_js.py")
WEBREPL_WEBPAGE_PATH = os.path.join(WEBREPL_DIR, "webrepl.html")

def init_webrepl_frontend():
    webrepldir_handler = SimplePopPushd()
    webrepldir_handler.pushd(WEBREPL_DIR)

    is_exists, ftype = FileHandler.path_is_exists(MAKE_HTML_WEBPAGE_PATH)
    if is_exists and ftype == 'f':
        print("RUN webrepl/make_html_js.py")
        exitcode, _, stderr = CommandHandler.run_command(f"{sys.executable} {MAKE_HTML_WEBPAGE_PATH}", shell=True)
        webrepldir_handler.popd()
        if exitcode == 0:
            return True
        print(f"Cannot init {MAKE_HTML_WEBPAGE_PATH}: {stderr}")
        return False
    print(f"WEBREPL MAKE MISSING: {MAKE_HTML_WEBPAGE_PATH}")
    return False

def open_webrepl_webpage(address=None, port=8266):
    # file:///Users/usrname/micrOS/micrOS/toolkit/workspace/webrepl/webrepl.html#10.0.1.76:8266
    fuid = ''
    if address is None:
        try:
            address, _, fuid, _ = ConnectionData.select_device()
        except KeyboardInterrupt:
            address = None

    device = "" if address is None else f"#{address}:{port}"
    webrepl_html = f"file://{WEBREPL_WEBPAGE_PATH}{device}"
    is_exists, ftype = FileHandler.path_is_exists(WEBREPL_WEBPAGE_PATH)
    if is_exists and ftype == "f":
        print(f"OPEN {fuid} webrepl {webrepl_html}")
        if sys.platform == "darwin":
            CommandHandler.run_command(f"open '{webrepl_html}'", shell=True)
        elif sys.platform == "win32":
            CommandHandler.run_command(f"start {webrepl_html}", shell=True)
        elif sys.platform == "linux":
            CommandHandler.run_command(f"xdg-open {webrepl_html}", shell=True)
        else:
            print("Unsupported OS")
            return False
        return True
    print(f"{WEBREPL_WEBPAGE_PATH} not exists.")
    return False


def open_webrepl():
    state = init_webrepl_frontend()
    if state:
        open_webrepl_webpage()



if __name__ == "__main__":
    open_webrepl()