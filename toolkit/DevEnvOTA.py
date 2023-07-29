import os
import sys
import time
MYPATH = os.path.dirname(__file__)
print("Module [DevEnvOTA] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYPATH))

try:
    from .DevEnvCompile import Compile
    from . import socketClient
    from .lib import LocalMachine
    from .lib.TerminalColors import Colors
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    from DevEnvCompile import Compile
    from lib import LocalMachine
    from lib.TerminalColors import Colors
    sys.path.append(MYPATH)
    import socketClient


#################################################
#       OTA(webrepl) + micrOS client handler    #
#################################################

class OTA(Compile):

    def __init__(self, cmdgui=None, gui_console=None, dry_run=False):
        super().__init__(dry_run=dry_run)
        self.webreplcli_repo_path = os.path.join(MYPATH, 'workspace/webrepl/webrepl_cli.py')
        self.cmdgui = cmdgui
        self.gui_console = gui_console
        # Skip the following modules in OTA update (safe mode) to have recovery mode
        self.safe_mode_file_exception_list = ['main.py', 'micrOSloader.mpy',
                                              'Network.mpy', 'ConfigHandler.mpy',
                                              'Debug.mpy']

    def safe_core_list(self):
        return self.safe_mode_file_exception_list

    def __clone_webrepl_repo(self):
        """Clone webrepl if not available"""
        webrepl_path = self.webreplcli_repo_path
        if os.path.isdir(os.path.dirname(webrepl_path)) and os.path.isfile(webrepl_path):
            return True
        # Download webrepl repo if necessary
        if not os.path.isfile(webrepl_path):
            # Change workdir
            workdir_handler = LocalMachine.SimplePopPushd()
            workdir_handler.pushd(os.path.dirname(os.path.dirname(webrepl_path)))

            command = 'git clone {url} {name}'.format(
                name='webrepl',
                url='https://github.com/micropython/webrepl.git')
            self.console("Clone webrepl repo: {}".format(command))
            if self.dry_run:
                exitcode, stdout, stderr = 0, 'dry-run', ''
            else:
                exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)

            # Restore workdir
            workdir_handler.popd()
            if exitcode == 0:
                self.console("\tClone {}DONE{}".format(Colors.OK, Colors.NC))
            else:
                self.console(
                    "GIT CLONE {}ERROR{}:\nstdout: {}\nstderr: {}".format(Colors.ERR, Colors.NC, stdout, stderr))
                return False
        return True

    def _version_compare(self, repo_version, fuid):
        """
        version SemVer: 1.2.3-4 - major[1.2]minor[.3]patch[-4]
            In case of [major] change force full update (micrOS safe core: micrOSloadoer, etc.)
            In case of [minor + patch] change install main micrOS resources + LMs
        :param fuid: friendly unique id / unique id
        :return: repo_version, device_version, force
        """
        # Get device version via socket
        if self.dry_run:
            status, answer_msg = True, '0.0.0-0'
        else:
            status, answer_msg = socketClient.run(['--dev', fuid, 'version'])
        device_version = answer_msg.strip() if status else None
        # Parse versions
        repo_major_version = repo_version.split('.')[0:2]
        device_major_version = device_version.split('.')[0:2] if device_version is not None and len(
            device_version.split('.')) == 3 else device_version
        force = False if repo_major_version == device_major_version else True
        return repo_version, device_version, force

    def _mpy_cross_compatibility_check(self, device=None):
        self.console("Compare mpycross - upython version compatibility")
        mpy_cross_version = None
        upython_version = None
        command = "{mpy_cross} --version".format(mpy_cross=self.mpy_cross_compiler_path.replace(" ", "\ "))
        result = LocalMachine.CommandHandler.run_command(command, shell=True)
        exitcode = result[0]
        raw_version = result[1]
        if exitcode == 0 and isinstance(raw_version, str):
            try:
                version = [v for v in raw_version.lower().split(" ") if v.startswith('v')][0]
                mpy_cross_version = version.split('-')[0].replace('v', '')
            except Exception as e:
                self.console("Cannot get mpy-cross version: {}".format(e))

        if self.dry_run:
            status, answer_msg = True, 'dry-run-upython: v1.19.1'
        else:
            status, answer_msg = socketClient.run(['--dev', device, 'system info'])
        if status:
            try:
                upython = [upython for upython in answer_msg.split("\n") if "upython" in upython][0]
                upython_version = upython.split(" ")[1].replace('v', '')
            except Exception as e:
                self.console("Cannot get upython version from board {}: {}".format(device, e))

        self.console("|- mpy-cross version: {}".format(mpy_cross_version))
        self.console("|- upython version on {}: {}".format(device, upython_version))

        if mpy_cross_version is not None and upython_version is None:
            # TODO: Get version over webrepl in case of micrOS interface not av ailable
            #       Corner case to be able to continue the update (if interrupted)
            self.console("Device upython version not available on micrOS interface ...", state="WARN")
            if input("Do you want to continue with this mpycross {} version? (Y/N)".format(mpy_cross_version)).lower().strip() == "y":
                return True
            return False

        try:
            mpc_v = mpy_cross_version.split('.')
            upy_v = upython_version.split('.')

            # Handle incompatibility - stop execution
            if upy_v[0] == mpc_v[0]:
                if int(mpc_v[1]) <= 18:
                    if int(upy_v[1]) <= 18:
                        # Both mpy-cross and upython less then/ equal 1.18 [OK - good enough]
                        return True
                    else:
                        msg = "[HINT] Obsoleted mpy-cross version, upython > 1.18\n\tUpdate mpy-cross version: pip uninstall mpy_cross; pip install mpy_cross"
                        if self.gui_console is not None: self.gui_console(msg)
                        self.console(msg, state='WARN')
                elif int(mpc_v[1]) > 18:
                    if int(upy_v[1]) > 18:
                        # Both mpy-cross and upython greater then 1.18 [OK]
                        return True
                    else:
                        msg = "[HINT] Obsoleted upython version, mpy-cross > 1.18\n\tUpdate micrOS over USB with new upython version > 1.18"
                        if self.gui_console is not None: self.gui_console(msg)
                        self.console(msg, state='WARN')
        except Exception as e:
            self.console(e, state='ERR')
        # Not compatible
        return False

    def update_with_webrepl(self, force=False, device=None, lm_only=False, loader_update=False, ota_password='ADmin123'):
        """
        OTA UPDATE via webrepl
            git clone https://github.com/micropython/webrepl.git
            info: https://techoverflow.net/2020/02/22/how-to-upload-files-to-micropython-using-webrepl-using-webrepl_cli-py/
            ./webrepl/webrepl_cli.py -p <password> <input_file> espressif.local:<output_file>
        """
        print("OTA UPDATE")
        upload_path_list = []

        # Precompile micrOS
        self.precompile_micros()

        # Get device IP and friendly name
        if device is None:
            # Select device dynamically - cmdline
            device_ip, port, fuid, uid = socketClient.ConnectionData.select_device()
            device = fuid, device_ip        # pass that to OTA update core
        else:
            # Select device from code / gui
            device_ip, fuid = device[1], device[0]
            device = fuid, device_ip       # pass that to OTA update core
        self.console("\tDevice was selected (fuid, ip): {} -> {}".format(fuid, device_ip), state='OK')

        # Get device appwd - device password for webrepl connection (not too safe - ???)
        status, answer_msg = socketClient.run(['--dev', fuid, 'conf', '<a>', 'appwd'])
        webrepl_password = answer_msg.strip() if status else None
        if webrepl_password is None:
            if self.cmdgui:
                # In case of update failure and retry (micrOS interface won't be active)
                webrepl_password = input("Please write your webrepl password (appwd - default ADmin123): ").strip()
            else:
                # Use password parameter input - cannot get from device
                webrepl_password = ota_password

        # Check micropython cross compile version compatibility
        if not self._mpy_cross_compatibility_check(device=fuid):
            self.console("Version mismatch: upython vs. mpycross", state='ERR')
            self.console("==> Update your micropython board via USB!", state='OK')
            if self.gui_console is not None: self.gui_console("Version mismatch: upython vs. mpycross")
            return False

        # Get versions: micrOS repo + live device, compare versions
        repo_version, device_version, auto_force = self._version_compare(self.get_micros_version_from_repo(), fuid)

        # Show connection and version data
        self.console("  Device: {} ({})".format(fuid, device_ip), state='OK')
        self.console("  Device version: {}".format(device_version), state='OK')
        self.console("  Repo version: {}".format(repo_version), state='OK')
        self.console("  WebRepl password: {}".format(webrepl_password), state='OK')

        # Check: Restrict micrOS update in case of light version on this branch (master) -> esp8266
        if 'light' in str(device_version):
            self.console("[SKIP UPDATE]\n\tmicrOS Light version detected - not supported scenario - restriction\
                         \n\t- use git lightweight branch for update, instead of master branch ...")
            self.console("Bye")
            return False

        # Check device and repo versions - update is necessary?
        if device_version == repo_version:
            if not force:
                self.console(
                    "\t[SKIP UPDATE] Device on same version with repo: {} == {}".format(device_version, repo_version))
                self.console("\tBye")
                self.execution_verdict.append("[OK] ota_update - update not necessary (no new version)")
                return False

        # Continue with micrOS main [y] or full micrOS (core loader) [yy - loader_update]
        if self.cmdgui:
            force_mode = auto_force
            user_input = input("Do you want to continue? Y/N: ").lower()
            # Detect update all mode - risky -> no recovery mode but updates all file on system
            if user_input == 'yy':
                msg_force = "[!!!] Force mode, update all files on micrOS system (recovery mode not available) Y/N: "
                user_input_force = input(msg_force).strip().lower()
                force_mode = True if user_input_force == 'y' else force_mode
            if 'n' == user_input:
                self.console("\tBye")
                return False
        else:
            force_mode = loader_update if loader_update else auto_force
        self.console("  loader update: {}".format(force_mode), state='OK')

        # Parse files from precompiled dir
        resource_list_to_upload = [os.path.join(self.precompiled_micrOS_dir_path, pysource) for pysource in
                                   LocalMachine.FileHandler.list_dir(self.precompiled_micrOS_dir_path)
                                   if pysource.endswith('.py') or pysource.endswith('.mpy')]
        # Apply upload settings on parsed resources
        for index, source in enumerate(resource_list_to_upload):
            source_name = os.path.basename(source)
            # Handle force mode + file exception list (skip)
            if not force_mode and source_name in self.safe_mode_file_exception_list:
                self.console(
                    "\t[SKIP UPLOAD][SKIP MICROS LOADER] {}".format(source_name), state='WARN')
                continue

            # Handle lm_only mode - skip upload for not LM_
            if lm_only:
                if not source_name.startswith("LM_"):
                    self.console(
                        "\t[SKIP UPLOAD][SKIP MICROS CORE] {}".format(source_name, lm_only), state='WARN')
                    continue

            # macOS icloud sync workaround ...
            if ' ' in source_name:
                self.console("\t[SKIP UPLOAD] space in resource name ... {}".format(source_name), state='WARN')
                continue

            # Add source to upload
            upload_path_list.append(source)
        # Upload files / sources
        return self.ota_webrepl_update_core(device, upload_path_list=upload_path_list, ota_password=webrepl_password)

    def _enable_micros_ota_update_via_webrepl(self, device=None):
        # Get specific device from device list
        self.console("Select device to update ...", state='IMP')
        socketClient.ConnectionData.read_micrOS_device_cache()
        # Get device IP and friendly name
        if device is None:
            # Select device dynamically - cmdline
            self.console("Select device manually:")
            device_ip, port, fuid, uid = socketClient.ConnectionData.select_device()
        else:
            # Select device from code / gui
            self.console("Device was selected with func param: {}".format(device))
            device_ip, fuid = device[1], device[0]
        self.console("\tDevice was selected (fuid, ip): {} -> {}".format(fuid, device_ip), state='OK')

        status, answer_msg = socketClient.run(['--dev', fuid, 'help'])
        if answer_msg is None:
            # micrOS auth:True not supported under ota update
            self.console("AuthFailed - no help msg was returned...", state='ERR')
            return False, device_ip, fuid
        if not status and answer_msg is None:
            # In case of update failure and retry (micrOS interface won't be active)
            status, answer_msg = True, 'webrepl'
        if status:
            if 'webrepl' in answer_msg:
                if self.dry_run:
                    status, answer_msg = True, 'dry-run'
                else:
                    if '--update' in answer_msg:
                        # START OTA UPDATE MODE ON DEVICE
                        self.console("[UPDATE] built-in restart and update monitor activation")
                        status, answer_msg = socketClient.run(['--dev', fuid, 'webrepl --update'])
                    else:
                        self.console("[UPDATE] live update - obsoleted...")
                        # START OTA UPDATE MODE ON DEVICE
                        status, answer_msg = socketClient.run(['--dev', fuid, 'webrepl'])
            else:
                self.console("Webrepl not available on device, update over USB.")
                self.execution_verdict.append("[ERR] ota_update - webrepl not available on node")
                return False, device_ip, fuid
        else:
            self.console("Get help from device failed.")
            self.execution_verdict.append("[ERR] ota_update - help command failed on device (no webrepl)")
            return False, device_ip, fuid
        time.sleep(3)
        return True, device_ip, fuid

    def _lock_handler(self, host, password, lock=False):
        """
        [1] Create .if_mode file (local file system)
            lock: True -> value: webrepl
            lock: False -> value: micros
        [2] Copy file to device
        """

        webrepl_if_mode = 'webrepl'  # micrOS system runs in webrepl mode - no micrOS interface running
        micros_if_mode = 'micros'  # micrOS running in normal mode - micrOS interface is active
        lock_value = webrepl_if_mode if lock else micros_if_mode  # Select lock value
        # Create webrepl copy command
        command = '{python} {api} -p {pwd} .if_mode {host}:.if_mode'.format(python=self.python_interpreter,
                                                                            api=self.webreplcli_repo_path.replace(" ", "\ "),
                                                                            pwd=password,
                                                                            host=host)

        if self.dry_run:
            self.console("Webrepl CMD: {}".format(command))
            return True

        workdir_handler = LocalMachine.SimplePopPushd()
        workdir_handler.pushd(self.precompiled_micrOS_dir_path)

        # Create / modify file
        with open(".if_mode", 'w') as f:
            f.write(lock_value)

        self.console("Webrepl CMD: {}".format(command))
        try:
            for _ in range(0, 5):
                exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
                if exitcode == 0:
                    LocalMachine.FileHandler.remove('.if_mode', ignore=True)
                    workdir_handler.popd()
                    return True
                else:
                    self.console("[INFO] [{}] {}\n{}".format(exitcode, stdout, stderr))
                    time.sleep(2)
        except Exception as e:
            self.console("Create lock/unlock failed: {}".format(e))
        self.console("[ERROR] Create lock/unlock failed")
        # Cleanup lock file: .if_mode + restore path
        LocalMachine.FileHandler.remove('.if_mode', ignore=True)
        workdir_handler.popd()
        return False

    def wait_for_micrOS_up_again(self, host):
        self.console("Device will reboot automatically, please wait 4-8 seconds.")
        time.sleep(4)
        up_again_status = False
        for is_up_again in range(1, 16):
            self.console("[{}/15] Try to connect ...".format(is_up_again))
            status, answer_msg = socketClient.run(['--dev', host, 'hello'])
            if status:
                self.console("Device {} is up again".format(host), state='OK')
                up_again_status = True
                break
            if not up_again_status:
                time.sleep(2)

        # Print manual steps if necessary
        if not up_again_status:
            self.console("Auto restart timeout, please reboot device manually.", state='WARN')
            self.console("Please reset your device.", state='IMP')
            self.console("\t[1]HINT: open in browser: http://micropython.org/webrepl/#{}:8266/".format(host))
            self.console("\t[2]HINT: log in and execute: import reset")
            self.console("\t[3]HINT: OR skip [2] point and reset manually")
            self.execution_verdict.append(
                "[WARN] ota_update - device auto restart failed,\nplease reset the device manually.")
        self.execution_verdict.append("[OK] ota_update was finished")
        return up_again_status

    def ota_webrepl_update_core(self, device=None, upload_path_list=[], ota_password='ADmin123', force_lm=False):
        """
        Generic file uploader for micrOS - over webrepl
            info: https://techoverflow.net/2020/02/22/how-to-upload-files-to-micropython-using-webrepl-using-webrepl_cli-py/
            ./webrepl/webrepl_cli.py -p <password> <input_file> espressif.local:<output_file>
        device = (ip, fuid)
        upload_path_list: file path list to upload
        ota_password - accessing webrepl to upload files
        force_lm - use prefix as 'LM_' for every file - for user file upload / GUI drag n drop
        """

        # GET webrepl repo
        if not self.__clone_webrepl_repo():
            self.console("Webrepl repo not available...", state='ERR')
            self.execution_verdict.append("[ERR] ota_update - clone webrepl repo")
            return False

        self.console("MICROS SOCKET WON'T BE AVAILABLE UNDER UPDATE.")

        # Enable micrOS OTA mode
        status, device_ip, fuid = self._enable_micros_ota_update_via_webrepl(device=device)

        # Create lock file for ota update
        self.console("[UPLOAD] Copy files to device...", state='IMP')
        self.console("\t[!] Create update lock (webrepl bootup) under OTA update", state='IMP')
        if not self._lock_handler(host=device_ip, password=ota_password, lock=True):
            self.console("OTA lock creation failed", state='ERR')
            self.execution_verdict.append("[ERR] ota_update - OTA update locked creation failed")
            return False

        # Upload path list
        for index, source in enumerate(upload_path_list):
            # calculate progress
            progress = round(((index + 1) / len(upload_path_list)) * 100)

            # Check no space in the file name
            if ' ' in os.path.basename(source):
                self.console("\t[{}%][SKIP UPLOAD] space in resource name ... {}".format(progress, source),
                             state='WARN')
                continue
            # Check no "hidden" content.
            if os.path.basename(source).startswith('__'):
                self.console("\t[{}%][SKIP UPLOAD] resource name starts with __ {}".format(progress, source),
                             state='WARN')
                continue

            # Change workdir
            workdir_handler = LocalMachine.SimplePopPushd()
            workdir_handler.pushd(os.path.dirname(source))

            # Copy retry mechanism
            exitcode = -1
            source_name = os.path.basename(source)
            source_name_target = source_name

            # Force LM update - user load modules - drag n drop files
            if force_lm and not source_name.startswith('LM_'):
                source_name_target = 'LM_{}'.format(source_name)

            command = '{python} {api} -p {pwd} {input_file} {host}:{target_path}'.format(
                python=self.python_interpreter,
                api=self.webreplcli_repo_path.replace(" ", "\ "),
                pwd=ota_password,
                input_file=source_name, host=device_ip,
                target_path=source_name_target)

            for ret_cnt in range(0, 5):
                self.console(
                    "[{}%] {} copy over webrepl {}:{}".format(progress, source_name, device_ip, source_name_target))
                if self.dry_run:
                    self.console("[{}%][UPLOAD] Webrepl CMD: {}".format(progress, command))
                    exitcode = 0
                    break
                else:
                    self.console("|- CMD: {}".format(command))
                    # --- UPLOAD ---
                    exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
                    if exitcode == 0:
                        self.console("|-- OK", state='OK')
                        break
                    else:
                        self.console("|-- WARN: {}\n{}".format(stderr, stdout), state='WARN')
                        self.console("|--- Retry upload file ...")
                        time.sleep(2)
            if exitcode != 0:
                self.console("|-- ERR: Update file failed, please try again.", state='ERR')
                self.execution_verdict.append("[ERR] ota_update - Update files are failed, pls try again.")
                # Restore workdir path
                workdir_handler.popd()
                return False
            # Restore workdir path
            workdir_handler.popd()

        self.console("\t[!] Delete update lock (webrepl bootup) under OTA update", state='IMP')
        if self._lock_handler(host=device_ip, password=ota_password, lock=False):
            self.console("\tOTA UPDATE WAS SUCCESSFUL", state='OK')
        else:
            self.console("\tOTA UPDATE WAS FAILED, PLEASE TRY AGAIN.", state='ERR')
            self.execution_verdict.append("[WARN] ota_update - failed to remove OTA update lock")
        return self.wait_for_micrOS_up_again(host=device_ip)


if __name__ == "__main__":
    o = OTA(dry_run=True)
    o.update_with_webrepl()
