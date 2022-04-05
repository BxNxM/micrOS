import sys
import os

# mac dmg install: https://apple.stackexchange.com/questions/73926/is-there-a-command-to-install-a-dmg
# win exe install: https://stackoverflow.com/questions/58697911/how-to-run-exe-file-from-python

try:
    from .LocalMachine import CommandHandler, FileHandler, SimplePopPushd
    from .TerminalColors import Colors
except Exception as e:
    print("Import warning: {}".format(e))
    from LocalMachine import CommandHandler, FileHandler, SimplePopPushd
    from TerminalColors import Colors

MYPATH = os.path.dirname(__file__)
print("Module [micrOSdashboard] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYPATH))
USB_DRIVER_DIR = os.path.join(MYPATH, '../../env/driver_cp210x')


def dmg_install_mac(dmg_path):
    if FileHandler.path_is_exists(dmg_path):
        # Path and params for install
        mount_command = "sudo hdiutil attach {}".format(dmg_path)
        unmount_command = "sudo hdiutil detach /Volumes/Silicon\ Labs\ VCP\ Driver\ Install\ Disk/"
        install_command = "/Volumes/Silicon\ Labs\ VCP\ Driver\ Install\ Disk/Install\ CP210x\ VCP\ Driver.app/Contents/MacOS/Install\ CP210x\ VCP\ Driver"

        # Do install
        print("[1/3] Mount dmg image: {}".format(dmg_path))
        exitcode, stdout, stderr = CommandHandler.run_command(mount_command, shell=True, debug=True)
        if exitcode == 0:
            print("[2/3] Execute installer: {}".format(install_command))
            exitcode, stdout, stderr = CommandHandler.run_command(install_command, shell=True, debug=True)
            if exitcode == 0:
                print("\tUSB driver install was successful")
            else:
                print("\tUSB driver install was failed: {}\n{}\n{}".format(stderr, stdout, exitcode))
                return False
            print("[3/3] Unmount dmg image")
            exitcode, stdout, stderr = CommandHandler.run_command(unmount_command, shell=True, debug=True)
        else:
            print("Mount error: {}\n{}\n{}".format(stderr, stdout, exitcode))
        return True
    else:
        print("\tInvalid dmg driver path: {}".format(dmg_path))
        return False


def exe_install_win(exe_path):
    if FileHandler.path_is_exists(exe_path):
        print("Install USB driver exe: {}".format(exe_path))
        SimplePopPushd().pushd(os.path.dirname(exe_path))
        exitcode, stdout, stderr = CommandHandler.run_command(os.path.basename(exe_path), shell=True, debug=True)
        SimplePopPushd().popd()
        if exitcode == 0:
            print("\tUSB driver install was successful")
            return True
        else:
            print("\tExe install error: {}\n{}\n{}".format(stderr, stdout, exitcode))
    else:
        print("\tInvalid exe driver path: {}".format(exe_path))
    return False


def restart():
    # Check driver is available
    is_installed, platform = check_serial_driver_is_installed()
    if is_installed:
        return
    # If driver not available, then reboot is necessary
    print("[!!!] After driver install, restart is necessary!".upper())
    if platform == 'mac':
        cmd = "sudo shutdown -r now"
    elif platform == 'win':
        cmd = "shutdown /r /t 1"
    else:
        cmd = "sudo reboot"
    # Execute reboot, after user agrees with it
    is_reboot = input("Restart Y/N: ")
    if is_reboot.lower() == 'y':
        exitcode, stdout, stderr = CommandHandler.run_command(cmd, shell=True, debug=True)
        if exitcode != 0:
            print("Restart failed: {}\n{}\n{}".format(stderr, stdout, exitcode))


def check_serial_driver_is_installed():
    if sys.platform.strip() == "darwin":
        print("{}Check USB serial driver on macOS{}".format(Colors.BOLD, Colors.NC))
        serial_app_path = '/Applications/CP210xVCPDriver.app/Contents/Library/SystemExtensions/com.silabs.cp210x.dext'
        is_exists, ptype = FileHandler.path_is_exists(serial_app_path)
        if is_exists and ptype == 'd':
            print("\t{}Serial driver was already installed: {}{}".format(Colors.OKGREEN, serial_app_path, Colors.NC))
            return True, 'mac'
        print("\t{}Do serial driver install {}".format(Colors.OKGREEN, serial_app_path, Colors.NC))
        return False, 'mac'
    elif sys.platform.startswith('win'):
        print("Check USB serial driver on Windows")
        serial_driver_key = 'cp210X'
        exitcode, stdout, stderr = CommandHandler.run_command("driverquery", debug=False)
        if exitcode in [0, 1]:
            if serial_driver_key in stdout:
                print("\tDo serial driver install ({})".format(serial_driver_key))
                return False, 'win'
            else:
                print("\tSerial driver was already installed ({}): {}".format(serial_driver_key, stdout))
                return True, 'win'

    else:
        # TODO
        print("{}Check USB serial driver on Linux:\n\tPlease install serial usb driver manually.{}".format(Colors.ERR,Colors.NC))

        return None, 'linux'


def install_usb_serial_driver():
    driver_sub_path = {'win': 'CP210x_Universal_Windows_Driver/CP210xVCPInstaller_x64.exe',
                       'mac': 'macOS_VCP_Driver/SiLabsUSBDriverDisk.dmg',
                       'linux': ''}
    # Check driver was installed
    is_installed, platform = check_serial_driver_is_installed()
    if is_installed is not None and is_installed is False:
        # Install driver, and Create driver path / platform
        if platform == 'mac':
            driver_path = os.path.join(USB_DRIVER_DIR, driver_sub_path['mac'])
            # DMG INSTALL
            status = dmg_install_mac(driver_path)
            if status:
                restart()
        elif platform == 'win':
            driver_path = os.path.join(USB_DRIVER_DIR, driver_sub_path['win'])
            # EXE INSTALL
            status = exe_install_win(driver_path)
            if status:
                restart()
    # Driver was already installed OR
    # Skip install in case of Linux (Linux users should install driver manually if necessary, but don't block them)
    return True


if __name__ == "__main__":
    status = install_usb_serial_driver()
    print("Install done: {}".format(status))
