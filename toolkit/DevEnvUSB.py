import os
import sys
import json
import time
import pprint
import serial.tools.list_ports as serial_port_list
MYPATH = os.path.dirname(__file__)
print("Module [DevEnvOTA] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYPATH))

try:
    from .DevEnvCompile import Compile
    from .lib import LocalMachine
    from .lib.TerminalColors import Colors
    from .lib.SerialDriverHandler import install_usb_serial_driver
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    from DevEnvCompile import Compile
    from lib import LocalMachine
    from lib.TerminalColors import Colors
    from lib.SerialDriverHandler import install_usb_serial_driver


class USB(Compile):
    usb_driver_ok = False

    def __init__(self, dry_run=False):
        super().__init__(dry_run=dry_run)
        self.nodemcu_device_subnames = ['SLAB_USBtoUART', 'USB0', 'usbserial', 'usbmodem']
        self.selected_device_type = None
        self.selected_micropython_bin = None
        self.micropython_bin_dir_path = os.path.join(MYPATH, "../micrOS/micropython")
        self.micrOS_node_config_archive = os.path.join(MYPATH, "user_data/node_config_archive")
        self.node_config_profiles_path = os.path.join(MYPATH, "../micrOS/release_info/node_config_profiles/")
        self.dev_types_and_cmds = \
            {'esp32':
                 {'erase': 'esptool.py --port {dev} erase_flash',
                  'deploy': 'esptool.py --chip esp32 --port {dev} --baud 460800 write_flash -z 0x1000 {micropython}',
                  'connect': 'screen {dev} 115200',
                  'ampy_cmd': 'ampy -p {dev} -b 115200 -d 2 {args}',
                  'cmd_line_info': '[!HINT!] PRESS [EN] BUTTON TO ENABLE DEVICE ERASE...'},
             'esp32s2':
                 {'erase': 'esptool.py --chip esp32s2 --port {dev} --after no_reset erase_flash',
                  'deploy': 'esptool.py --chip esp32s2 --port {dev} --after no_reset --baud 460800 write_flash -z 0x1000 {micropython}',
                  'connect': 'screen {dev} 115200',
                  'ampy_cmd': 'ampy -p {dev} -b 115200 -d 2 {args}',
                  'cmd_line_info': '[!HINT!] Hold on Button 0 -> Press Button Reset -> Release Button 0 TO ENABLE DEVICE ERASE...'},
             'tinypico':
                 {'erase': 'esptool.py --port {dev} erase_flash',
                  'deploy': 'esptool.py --chip esp32 --port {dev} --baud 460800 write_flash -z 0x1000 {micropython}',
                  'connect': 'screen {dev} 115200',
                  'ampy_cmd': 'ampy -p {dev} -b 115200 -d 2 {args}',
                  'cmd_line_info': ''},
             'rp2-pico-w':
                 {'erase': None,
                  'deploy': self._deploy_micropython_dev_usb_storage,
                  'connect': 'screen {dev}',
                  'ampy_cmd': 'ampy -p {dev} -b 115200 -d 2 {args}',
                  'cmd_line_info': '[!!!] Experimental device - no stable micropython yet'},
             'esp32s3_spiram_oct':
                 {'erase': 'esptool.py --chip esp32s3 --port {dev} erase_flash',
                  'deploy': 'esptool.py --chip esp32s3 --port {dev} write_flash -z 0 {micropython}',
                  'connect': 'screen {dev} 115200',
                  'ampy_cmd': 'ampy -p {dev} -b 115200 -d 2 {args}',
                  'cmd_line_info': '[!!!] Experimental device, no pinmap was adapted (fallback to esp32)'},
             }
        if not USB.usb_driver_ok:
            # Optimization - driver check
            install_usb_serial_driver()
            USB.usb_driver_ok = True

    #############################
    #       Main interfaces     #
    #############################
    def select_board_n_micropython(self, board=None, binary=None):
        if self.selected_device_type is None:
            if board is None:
                # Select board type - manual
                self.console("Please select device type from the list:")
                for index, device_type in enumerate(self.dev_types_and_cmds.keys()):
                    self.console(" {} - {}".format(index, device_type))
                if self.selected_device_type is None:
                    self.selected_device_type = list(self.dev_types_and_cmds.keys())[int(input("Select index: "))]
            else:
                # Select board type - from input param (gui)
                self.selected_device_type = board
        if self.selected_micropython_bin is None:
            if binary is None:
                # Select micropython - manual
                micropython_bin_for_type = [mbin for mbin in self.get_micropython_binaries() if
                                            f'{self.selected_device_type.lower()}-' in mbin]
                selected_index = 0
                if len(micropython_bin_for_type) > 1:
                    self.console("Please select micropython for deployment")
                    for index, mpbin in enumerate(micropython_bin_for_type):
                        self.console(" {} - {}".format(index, mpbin))
                    selected_index = int(input("Selected index: "))
                    self.selected_micropython_bin = micropython_bin_for_type[selected_index]
                else:
                    self.selected_micropython_bin = micropython_bin_for_type[selected_index]
            else:
                # Select micropython - from input param (gui)
                self.selected_micropython_bin = binary

        self.console("Device: {}".format(self.selected_device_type))
        self.console("micropython: {}".format(self.selected_micropython_bin))
        return self.selected_device_type, self.selected_micropython_bin

    def erase_dev(self):
        self.console("------------------------------------------")
        self.console("-           ERASE MICROS DEVICE          -", state='imp')
        self.console("------------------------------------------")
        self.select_board_n_micropython()
        commandline_comment = ""

        erase_cmd = self.dev_types_and_cmds[self.selected_device_type]['erase']
        if erase_cmd is None:
            """Handle missing erase command - in case of raspberry pico"""
            self.console("Cannot erase device, erase command not found (raspberry pico w)")
            return True

        selected_device = self.get_devices()[0]
        print("selected_device_port: {}".format(selected_device))
        command = erase_cmd.format(dev=selected_device)
        self.console("CMD: {}".format(command))
        if self.dry_run:
            exitcode = 0
            stdout = "Dummy stdout"
            stderr = "Dummy stderr"
        else:
            commandline_comment = self.dev_types_and_cmds[self.selected_device_type]['cmd_line_info']
            self.console(commandline_comment, state='imp')
            if self.gui_console is not None:
                self.gui_console(commandline_comment)
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
        if exitcode == 0:
            self.console("Erase done.\n{}".format(stdout), state='ok')
            return True
        else:
            self.console("Erase failed.\n{} - {}".format(stdout, stderr), state='err')
            self.console(commandline_comment, state='warn')
            return False

    def deploy_micropython_dev(self):
        self.console("------------------------------------------")
        self.console("-            DEPLOY MICROPYTHON          -", state='imp')
        self.console("------------------------------------------")
        self.select_board_n_micropython()

        deploy_cmd = self.dev_types_and_cmds[self.selected_device_type]['deploy']
        # Handle method call as deploy_cmd (for raspberry pi pico micropython deployment)
        if not isinstance(deploy_cmd, str):
            return self._deploy_micropython_dev_usb_storage()

        selected_device = self.get_devices()[0]
        selected_micropython = self.selected_micropython_bin
        command = deploy_cmd.format(dev=selected_device, micropython=selected_micropython)
        self.console("CMD: {}".format(command))
        if self.dry_run:
            exitcode = 0
            stdout = "Dummy stdout"
            stderr = "Dummy stderr"
        else:
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
        if exitcode == 0:
            self.console("Deployment done.\n{}".format(stdout), state='ok')
            time.sleep(1)
            return True
        else:
            self.console("Deployment failed.\n{} - {}".format(stdout, stderr), state='err')
            return False

    def put_micros_to_dev(self):
        self.select_board_n_micropython()
        status = True
        config_is_valid = self.__validate_json()
        if not config_is_valid:
            sys.exit(6)

        # Handle HARD RESET requirement
        if isinstance(self.dev_types_and_cmds[self.selected_device_type]['deploy'], str) and "no_reset" in self.dev_types_and_cmds[self.selected_device_type]['deploy']:
            self.console("[!HINT!] USB reset not available. [!!!] PRESS RST BUTTON!", state='warn')
            if self.gui_console is not None:
                self.gui_console("[!HINT!] USB reset not available. [!!!] PRESS RST BUTTON!")
            for k in range(1, 11):
                self.console(f"... wait for reset {10-k} sec", state='imp')
                time.sleep(1)

        ampy_cmd = self.dev_types_and_cmds[self.selected_device_type]['ampy_cmd']
        device = self.get_devices()[0]
        source_to_put_device = LocalMachine.FileHandler.list_dir(self.precompiled_micrOS_dir_path)
        # Set source order - main, boot
        source_to_put_device.append(source_to_put_device.pop(source_to_put_device.index('main.py')))

        # Change workdir
        workdir_handler = LocalMachine.SimplePopPushd()
        workdir_handler.pushd(self.precompiled_micrOS_dir_path)

        for index, source in enumerate(source_to_put_device):
            percent = int((index + 1) / len(source_to_put_device) * 100)
            self.console("[{}%] micrOS deploy via USB".format(percent))
            ampy_args = 'put {from_}'.format(from_=source)
            command = ampy_cmd.format(dev=device, args=ampy_args)
            command = '{cmd}'.format(cmd=command)
            if ' ' in source:
                self.console("[{}%][SKIP] micrOS deploy via USB: {}".format(percent, command))
                continue
            status &= self.__safe_execute_ampy_cmd(command, source)
            if not status:
                self.console("MICROS INSTALL FAILED", state='err')
                sys.exit(5)
        # Restore original workdir
        workdir_handler.popd()
        return True

    def update_micros_via_usb(self, force=False):
        self.select_board_n_micropython()
        exitcode, stdout, stderr = self.__get_node_config()
        print(self.__get_node_config())
        if exitcode == 0:
            self.console("Get Node config (node_config.json):")
            pprint.PrettyPrinter(indent=4).pprint(json.loads(stdout))
            repo_version, node_version = self.get_micrOS_version(stdout)
            self.console("Repo version: {} Node_version: {}".format(repo_version, node_version))
            if repo_version != node_version or force:
                self.console("Update necesarry {} -> {}".format(node_version, repo_version), state='ok')
                state = self.__override_local_config_from_node(node_config=stdout)
                if state:
                    self.deploy_micros(restore=False)
                else:
                    self.console("Saving node config failed - SKIP update/redeploy", state='err')
            else:
                self.console("System is up-to-date.")
                self.execution_verdict.append("[OK] usb_update system is up-to-date")
                return True
        else:
            self.console("Node config error: {} - {}".format(stdout, stderr))
            self.execution_verdict.append("[ERR] usb_update get node config error.")
            return False
        self.execution_verdict.append("[OK] usb_update was finished")
        return True

    def deploy_micros(self, restore=True, purge_conf=False):
        """
        Clean board deployment with micropython + micrOS
        :param restore: restore and create node config
        :param purge_conf: purge node config - deletion
        :return: None
        """
        self.select_board_n_micropython()
        if purge_conf:
            self._purge_node_config_from_workdir()
        if restore:
            self._restore_and_create_node_config()

        is_erased = False
        for _ in range(0, 4):
            # Retry mechanism
            is_erased = self.erase_dev()
            time.sleep(2)
            if is_erased:
                break
        if is_erased:
            if self.deploy_micropython_dev():
                time.sleep(2)
                self.precompile_micros()
                time.sleep(2)
                self.put_micros_to_dev()
                self._archive_node_config()
            else:
                self.console("Deploy micropython error", state='err')
                self.execution_verdict.append("[ERROR] usb_deploy - micropython install failed")
        else:
            self.console("Erase device error", state='err')
        self.execution_verdict.append("[OK] usb_deploy was finished")

    def get_micropython_binaries(self):
        self.console("------------------------------------------")
        self.console("-         GET MICROPYTHON BINARIES       -", state='imp')
        self.console("------------------------------------------")
        micropython_bins_list = []

        self.console(f"Micropython bin path: {self.micropython_bin_dir_path}")
        mp_bin_list = [binary for binary in LocalMachine.FileHandler.list_dir(self.micropython_bin_dir_path) if
                       binary.endswith('.bin') or binary.endswith('.uf2')]
        for mp_bin in mp_bin_list:
            micropython_bins_list.append(os.path.join(self.micropython_bin_dir_path, mp_bin))
        if len(micropython_bins_list) > 0:
            self.console("Micropython binary was found.", state='ok')
        else:
            self.console("Micropython binary was not found.", state='err')
        return micropython_bins_list

    def get_devices(self):
        self.console("------------------------------------------")
        self.console("-  LIST CONNECTED MICROS DEVICES VIA USB -", state='imp')
        self.console("------------------------------------------")
        micros_devices = []

        if self.dry_run:
            return ['dummy_device']

        if not sys.platform.startswith('win'):
            # List USB devices on macOS and Linux
            dev_path = '/dev/'
            content_list = [dev for dev in LocalMachine.FileHandler.list_dir(dev_path) if "tty" in dev]
            for present_dev in content_list:
                for dev_identifier in self.nodemcu_device_subnames:
                    if dev_identifier in present_dev:
                        dev_abs_path = os.path.join(dev_path, present_dev)
                        micros_devices.append(dev_abs_path)
                        self.console("Device was found: {}".format(dev_abs_path), state="imp")
                        break
        else:
            # List USB devices on Windows
            ports = list(serial_port_list.comports())
            for item in ports:
                self.console(f'[Win] Com device: {item.description}')
                if "CP210" in str(item.description) or "CH340" in str(item.description):
                    micros_devices.append(item.device)
                    self.console("Device was found: {}".format(item.device, state="imp"))
        # Eval device list, return with devices
        if len(micros_devices) > 0:
            self.console("Device was found. :)", state="ok")
        else:
            self.console("No device was connected. :(", state="err")
        return micros_devices

    #############################
    #       Internal stuff      #
    #############################

    def _purge_node_config_from_workdir(self):
        path = os.path.join(self.precompiled_micrOS_dir_path, 'node_config.json')
        LocalMachine.FileHandler().remove(path, ignore=False)

    def _restore_and_create_node_config(self):
        self.console("RESTORE NODE_CONFIG.JSON")
        self.__generate_default_config()
        conf_list = []
        index = -1
        if os.path.isdir(self.micrOS_node_config_archive):
            conf_list = [conf for conf in LocalMachine.FileHandler.list_dir(self.micrOS_node_config_archive) if
                         conf.endswith('json')]
        self.console("Select config file to deplay:")
        for index, conf in enumerate(conf_list):
            self.console("  [{}{}{}] {}".format(Colors.BOLD, index, Colors.NC, conf))
        self.console("  [{}{}{}] {}".format(Colors.BOLD, index + 1, Colors.NC, 'NEW'))
        self.console("  [{}{}{}] {}".format(Colors.BOLD, index + 2, Colors.NC, 'SKIP'))
        conf_list.append(os.path.join('node_config.json'))
        conf_list.append(os.path.join('SKIP'))
        selected_index = int(input("Select index: "))
        # Use (already existing) selected config to restore
        selected_config = conf_list[selected_index]
        if '-' in selected_config:
            # Restore saved config
            target_path = os.path.join(self.precompiled_micrOS_dir_path, selected_config.split('-')[1])
            source_path = os.path.join(self.micrOS_node_config_archive, selected_config)
        elif selected_index == len(conf_list) - 1:
            # SKIP restore config - use the local version in mpy-micrOS folder
            target_path = os.path.join(self.precompiled_micrOS_dir_path, 'node_config.json')
            source_path = None
        else:
            # Create new config - from micrOS folder path -> mpy-micrOS folder
            target_path = os.path.join(self.precompiled_micrOS_dir_path, selected_config)
            source_path = os.path.join(self.micrOS_dir_path, selected_config)
        self.console("Restore config: {} -> {}".format(source_path, target_path))
        if source_path is not None:
            LocalMachine.FileHandler.copy(source_path, target_path)

        # In case of NEW config - profile injection option
        if selected_index == len(conf_list) - 2:
            # Inject profile data
            if self._inject_profile(target_path) is None:
                # Dump untouched config content
                with open(target_path, 'r') as f:
                    self.console(
                        "[ INFO ] Actual config:\n{}".format(json.dumps(json.load(f), indent=4, sort_keys=True)))

        # Manual config editing breakpoint
        self.console("=================== INFO =====================")
        self.console("[ INFO ] To edit your config, open: {}".format(target_path))
        input("[ QUESTION ] To continue, press enter.")
        # Dump config content
        try:
            with open(target_path, 'r') as f:
                self.console(
                    "[ INFO ] Deployment with config:\n{}".format(json.dumps(json.load(f), indent=4, sort_keys=True)))
        except Exception as e:
            self.console(f"[SKIP] Local config generation: {e}")

    def _inject_profile(self, target_path):
        profile_list = [profile for profile in LocalMachine.FileHandler.list_dir(self.node_config_profiles_path) if
                        profile.endswith('.json')]
        for index, profile in enumerate(profile_list):
            self.console("[{}]\t{}".format(index, profile))
        profile = input("[ QUESTION ] Select {}profile{} or to skip press enter: ".format(Colors.BOLD, Colors.NC))
        if len(profile.strip()) == 0:
            self.console("SKIP profile selection.")
            return None
        else:
            self.console("Profile was selected: {}{}{}".format(Colors.OK, profile_list[int(profile)], Colors.NC))
        # Read default conf
        default_conf_path = os.path.join(self.micros_sim_workspace, 'node_config.json')
        if not os.path.isfile(default_conf_path):
            self.micrOS_sim_default_conf_create()
        with open(default_conf_path, 'r') as f:
            default_conf_dict = json.load(f)
        # Read profile
        profile_path = os.path.join(self.node_config_profiles_path, profile_list[int(profile)])
        with open(profile_path, 'r') as f:
            profile_dict = json.load(f)
        for key, value in profile_dict.items():
            if value is None:
                # Get input - cast variable type
                value_ = None
                while value_ is None:
                    value = input(" |-> Fill {}{}{} config parameter, type {}: "
                                  .format(Colors.BOLD, key, Colors.NC, type(default_conf_dict.get(key))))
                    value_ = self.__convert_data_type(default_conf_dict.get(key), value)
                value = value_
                # Save value
                profile_dict[key] = value
                self.console(" |--> SET {}: {}".format(key, value))
        # Create New profiled config - merge dicts
        default_conf_dict.update(profile_dict)
        # Dump Data
        self.console("Configured node_config.json:")
        self.console(json.dumps(default_conf_dict, indent=4, sort_keys=True))
        # Write data
        self.console("Write config to {}".format(target_path))
        with open(target_path, 'w') as f:
            json.dump(default_conf_dict, f)
        # Show command hints for selected profile
        example_commands_file_path = profile_path.replace('-node_config.json', '_command_examples.txt')
        with open(example_commands_file_path, 'r') as f:
            self.console("{} profile command {}HINTS{}:\n{}".format(profile_path, Colors.OK, Colors.NC, f.read()))
        return True

    def __convert_data_type(self, target_type_value, input_var):
        try:
            if isinstance(target_type_value, bool):
                self.console("BOOL: {}".format(input_var))
                return bool(input_var)
            elif isinstance(target_type_value, int):
                self.console("INT: {}".format(input_var))
                return int(input_var)
            elif isinstance(target_type_value, float):
                self.console("FLOAT: {}".format(input_var))
                return float(input_var)
            elif isinstance(target_type_value, str):
                self.console("STR: {}".format(input_var))
                return str(input_var)
            else:
                self.console("NON SUPPORTED TYPE")
                return None
        except Exception as e:
            self.console("TYPE CASTING ERROR: {}".format(e))
            return None

    def __generate_default_config(self):
        self.console("GENERATE DEFAULT NODE_CONFIG.JSON")

        # Change workdir
        workdir_handler = LocalMachine.SimplePopPushd()
        workdir_handler.pushd(self.micrOS_dir_path)

        create_default_config_command = "{} ConfigHandler.py".format(self.python_interpreter)
        if not self.dry_run:
            # Remove actual defualt config
            LocalMachine.FileHandler.remove(os.path.join(self.micrOS_dir_path, 'node_config.json'))
            # Create default config
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(create_default_config_command,
                                                                               shell=True)
        else:
            exitcode = 0
        # Restore workdir
        workdir_handler.popd()
        if exitcode == 0:
            return True
        return False

    def _deploy_micropython_dev_usb_storage(self):
        """
        Handle micropython block storage install (rp2-w)
        """
        storage_path = "/Volumes/RPI-RP2"
        # TODO: handle path in windows
        selected_micropython = self.selected_micropython_bin
        if os.path.isdir(storage_path):
            self.console("Install micropython by binary copy: {} -> {}".format(selected_micropython, storage_path))
        state = LocalMachine.FileHandler().copy(selected_micropython, storage_path)
        if state:
            for _ in range(0, 10):
                self.console("Wait for usb device...")
                time.sleep(3)
                if len(self.get_devices()) > 0:
                    break
        return state

    def __validate_json(self):
        is_valid = True
        local_config_path = os.path.join(self.precompiled_micrOS_dir_path, 'node_config.json')
        try:
            if os.path.isfile(local_config_path):
                with open(local_config_path, 'r') as f:
                    text = f.read()
                    json.loads(text)
        except ValueError as e:
            self.console("Invalid config: {}\n{}".format(local_config_path, e))
            is_valid = False
        return is_valid

    def __safe_execute_ampy_cmd(self, command, source, retry=8):
        retry_orig = retry
        status = False
        for retry in range(1, retry_orig):
            if not self.dry_run:
                try:
                    exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
                except Exception as e:
                    self.console(e)
                    exitcode = 1
                    stderr = str(e)
            else:
                exitcode = 0
                stderr = ''
            if exitcode == 0 and stderr == '':
                self.console("[ OK ] PUT {}".format(source), state='ok')
                self.console(" |-> CMD: {}".format(command))
                status = True
                break
            else:
                self.console("[ ERROR/RETRY ][{}/{}] PUT {}\n{}".format(retry, retry_orig, source, stderr), state='err')
                self.console(" |-> CMD: {}".format(command))
                status = False
            time.sleep(0.2)
        return status

    def connect_dev(self):
        self.select_board_n_micropython()
        self.console("WELCOME $USER - $(DATE)")
        self.console("TO EXIT: ctrl-a d OR ctrl-a ctrl-d")
        time.sleep(2)

        connect_cmd = self.dev_types_and_cmds[self.selected_device_type]['connect']
        selected_device = self.get_devices()[0]
        command = connect_cmd.format(dev=selected_device)
        self.console("CMD: {}".format(command))
        if not self.dry_run:
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
        self.disconnect_dev()

    def disconnect_dev(self):
        terminate_cmd = 'kill {pid}'
        command = terminate_cmd.format(pid=self.__dev_used_from())
        self.console("CMD: {}".format(command))
        if not self.dry_run:
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
        else:
            exitcode = 0
        self.console("Disconnect exitcode: {}".format(exitcode))

    def __dev_used_from(self):
        fuser_cmd = 'fuser {dev}'
        selected_device = self.get_devices()[0]
        command = fuser_cmd.format(dev=selected_device)
        self.console("CMD: {}".format(command))
        if self.dry_run:
            exitcode = 0
            stdout = "PID DUMMY"
        else:
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
        if exitcode != 0:
            self.console("Can't get device used from... {}".format(stderr))
            sys.exit(3)
        # return process id
        processid = stdout.strip().split(' ')[0]
        self.console("Device was used from: {}".format(processid))
        return processid

    def __get_node_config(self):
        ampy_cmd = self.dev_types_and_cmds[self.selected_device_type]['ampy_cmd']
        device = self.get_devices()[0]
        arguments = 'get node_config.json'
        command = ampy_cmd.format(dev=device, args=arguments)
        if not self.dry_run:
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
            self._archive_node_config()
        else:
            exitcode = 0
            stdout = '{"key": "Dummy stdout"}'
            stderr = ''
        if '\n' in stdout:
            stdout = stdout.strip().splitlines()
            stdout = str([line for line in stdout if '{' in line and '}' in line][0])
        return exitcode, stdout, stderr

    def backup_node_config(self):
        self.select_board_n_micropython()
        if len(self.get_devices()) > 0:
            exitcode, stdout, stderr = self.__get_node_config()
            print("1-: {}\n{}\n{}".format(exitcode, stdout, stderr))
            if exitcode == 0:
                self.console("Get Node config (node_config.json):")
                pprint.PrettyPrinter(indent=4).pprint(json.loads(stdout))
                state = self.__override_local_config_from_node(node_config=stdout)
                if state:
                    self._archive_node_config()
                    return True
        self.console("exitcode: {}\n{}\n{}".format(exitcode, stdout, stderr))
        return False

    def _archive_node_config(self):
        self.console("ARCHIVE NODE_CONFIG.JSON")
        local_node_config = os.path.join(self.precompiled_micrOS_dir_path, 'node_config.json')
        if os.path.isfile(local_node_config):
            with open(local_node_config, 'r') as f:
                node_devfid = json.load(f)['devfid']
            archive_node_config = os.path.join(self.micrOS_node_config_archive,
                                               '{}-node_config.json'.format(node_devfid))
            LocalMachine.FileHandler.create_dir(self.micrOS_node_config_archive)
            self.console("Archive node_config... to {}".format(archive_node_config))
            if not self.dry_run:
                LocalMachine.FileHandler.copy(local_node_config, archive_node_config)

    def __override_local_config_from_node(self, node_config=None):
        node_config_path = os.path.join(self.precompiled_micrOS_dir_path, 'node_config.json')
        self.console("Overwrite node_config.json with connected node config: {}".format(node_config_path), state='ok')
        if not self.dry_run and node_config is not None:
            with open(node_config_path, 'w') as f:
                f.write(node_config)
        return True

    def list_micros_filesystem(self):
        self.__initialize_dev_env_for_deployment_vis_usb()
        ampy_cmd = self.dev_types_and_cmds[self.selected_device_type]['ampy_cmd']
        device = self.get_devices()[0]
        command = ampy_cmd.format(dev=device, args='ls')
        if not self.dry_run:
            self.console("CMD: {}".format(command))
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
        else:
            exitcode = 0
            stdout = 'Dummy stdout'
        if exitcode == 0:
            self.console("micrOS node content:\n{}".format(stdout), state='ok')
        else:
            self.console("micrOS node content list error:\n{}".format(stderr), state='err')


if __name__ == "__main__":
    u = USB(dry_run=True)
    print(u.select_board_n_micropython())
    print(u.get_devices())
    u.deploy_micros()
