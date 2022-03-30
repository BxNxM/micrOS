import sys
import os

try:
    from .LocalMachine import CommandHandler
except Exception as e:
    print("Import warning: {}".format(e))
    from LocalMachine import CommandHandler


MYPATH = os.path.dirname(__file__)
print("Module [micrOSdashboard] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYPATH))
USB_DRIVER_DIR = os.path.join(MYPATH, '../../env/driver_cp210x')


def check_serial_driver_is_installed():
    if sys.platform.strip() == "darwin":
        print("Check USB serial driver on macOS")
        exitcode, stdout, stderr = CommandHandler.run_command("kextstat | grep 'usb.serial'", shell=True, debug=False)
        if exitcode == 0:
            if 'usb.serial' not in stdout:
                print("\tDo serial driver install")
                install_usb_serial_driver()
            else:
                print(USB_DRIVER_DIR)
                print("\tSerial driver was already installed: {}".format(stdout))
    elif sys.platform.startswith('win'):
        print("Check USB serial driver on Windows")
    else:
        print("Check USB serial driver on Linux: TODO\n\tPlease install serial usb driver manually.")


def install_usb_serial_driver():
    print("Install TODO: {}".format(USB_DRIVER_DIR))


if __name__ == "__main__":
    check_serial_driver_is_installed()
