#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import json
import pprint
import time
import serial.tools.list_ports as serial_port_list

MYPATH = os.path.dirname(__file__)
print("Module [MicrOSDevEnv] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYPATH))

try:
    from . import socketClient
    from .lib import LocalMachine
    from .lib.TerminalColors import Colors
    from .lib.SerialDriverHandler import install_usb_serial_driver
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    from lib import LocalMachine
    from lib.TerminalColors import Colors
    from lib.SerialDriverHandler import install_usb_serial_driver

    sys.path.append(MYPATH)
    import socketClient

try:
    import mpy_cross
except Exception as e:
    print("{}[!!!] mpy-cross error{}: {}".format(Colors.ERR, Colors.NC, e))
    mpy_cross = None


class MicrOSDevTool:

    def __init__(self, dummy_exec=False, gui_console=None, cmdgui=True):
        self.dummy_exec = dummy_exec
        self.gui_console = gui_console
        self.cmdgui = cmdgui
        # Skip the following modules in OTA update (safe mode) to have recovery mode
        self.safe_mode_file_exception_list = ['boot.py', 'micrOSloader.mpy',
                                              'Network.mpy', 'ConfigHandler.mpy',
                                              'Debug.mpy']
        # USB serial (sub)names to recognize in /dev/tty...
        self.nodemcu_device_subnames = ['SLAB_USBtoUART', 'USB0', 'usbserial']
        # Commands for devices
        self.dev_types_and_cmds = \
            {'esp32':
                 {'erase': 'esptool.py --port {dev} erase_flash',
                  'deploy': 'esptool.py --chip esp32 --port {dev} --baud 460800 write_flash -z 0x1000 {micropython}',
                  'connect': 'screen {dev} 115200',
                  'ampy_cmd': 'ampy -p {dev} -b 115200 -d 2 {args}'},
             'tinypico':
                 {'erase': 'esptool.py --port {dev} erase_flash',
                  'deploy': 'esptool.py --chip esp32 --port {dev} --baud 460800 write_flash -z 0x1000 {micropython}',
                  'connect': 'screen {dev} 115200',
                  'ampy_cmd': 'ampy -p {dev} -b 115200 -d 2 {args}'},
             }

        # DevEnv base pathes
        self.MicrOS_dir_path = os.path.join(MYPATH, "../micrOS/source")
        self.MicrOS_node_config_archive = os.path.join(MYPATH, "user_data/node_config_archive")
        self.precompiled_MicrOS_dir_path = os.path.join(MYPATH, "workspace/precompiled")
        self.micropython_bin_dir_path = os.path.join(MYPATH, "../micrOS/micropython")
        self.micropython_repo_path = os.path.join(MYPATH, 'workspace/micropython')
        self.webreplcli_repo_path = os.path.join(MYPATH, 'workspace/webrepl/webrepl_cli.py')
        if mpy_cross is None:
            self.mpy_cross_compiler_path = None
        else:
            self.mpy_cross_compiler_path = mpy_cross.mpy_cross  # mpy-cross binary path for cross compilation
        self.micros_sim_resources = os.path.join(MYPATH, 'simulator_lib')
        self.micros_sim_workspace = os.path.join(MYPATH, 'workspace/simulator')
        self.precompile_LM_wihitelist = self.read_LMs_whitelist()
        self.node_config_profiles_path = os.path.join(MYPATH, "../micrOS/release_info/node_config_profiles/")
        self.sfuncman_output_path = os.path.join(MYPATH, "../micrOS/client/sfuncman/")
        self.micropython_git_repo_url = 'https://github.com/micropython/micropython.git'

        # Filled by methods
        self.selected_device_type = None
        self.selected_micropython_bin = None
        self.devenv_usb_deployment_is_active = False

        # External access for exec results
        self.execution_verdict = []
        self.LM_functions_static_dump_gen()

    #####################################################
    #               BASE / INTERNAL METHODS             #
    #####################################################
    def read_LMs_whitelist(self):
        lm_to_compile_conf_path = os.path.join(MYPATH, "LM_to_compile.dat")
        whitelist = []
        if os.path.isfile(lm_to_compile_conf_path):
            with open(lm_to_compile_conf_path, 'r') as f:
                whitelist = [str(k.strip()) for k in f.read().strip().split() if
                             k.strip().startswith('LM_') and k.strip().endswith('.py')]
        return whitelist

    def __initialize_dev_env_for_deployment_vis_usb(self):
        if self.devenv_usb_deployment_is_active:
            self.console("Devide and micropython was already selected")
            self.console("Device: {}".format(self.selected_device_type))
            self.console("micropython: {}".format(self.selected_micropython_bin))
        else:
            # Find micropython binaries
            install_usb_serial_driver()  # Serial-USB Driver install
            self.get_micropython_binaries()
            # Find micrOS devices
            self.__select_devicetype_and_micropython()
            self.devenv_usb_deployment_is_active = True

    def __select_devicetype_and_micropython(self):
        print(self.dev_types_and_cmds.keys())
        if len(self.dev_types_and_cmds.keys()) > 1:
            self.console("Please select device type from the list:")
            for index, device_type in enumerate(self.dev_types_and_cmds.keys()):
                self.console(" {} - {}".format(index, device_type))
            if self.selected_device_type is None:
                self.selected_device_type = list(self.dev_types_and_cmds.keys())[int(input("Select index: "))]

        micropython_bin_for_type = [mbin for mbin in self.get_micropython_binaries() if
                                    self.selected_device_type.lower() in mbin]
        selected_index = 0
        if len(micropython_bin_for_type) > 1:
            self.console("Please select micropython for deployment")
            for index, mpbin in enumerate(micropython_bin_for_type):
                self.console(" {} - {}".format(index, mpbin))
            if self.cmdgui:
                selected_index = int(input("Selected index: "))
                if not self.devenv_usb_deployment_is_active:
                    self.selected_micropython_bin = micropython_bin_for_type[selected_index]
        else:
            self.selected_micropython_bin = micropython_bin_for_type[selected_index]

        self.console("-" * 60)
        self.console("Selected device type: {}".format(self.selected_device_type))
        self.console("Selected micropython bin: {}".format(self.selected_micropython_bin))
        self.console("-" * 60)

    def console(self, msg, state=None):
        '''
        Console print with highlights
        - None: use no highlights
        - OK: ok - green
        - WARN: warning - yellow
        - ERR: error - red
        - IMP: important - bold
        '''
        prompt = "{COL}[MicrOSTools]{END} {msg}"
        if state is None:
            print(prompt.format(COL='', msg=msg, END=''))
        elif state.upper() == 'OK':
            print(prompt.format(COL=Colors.OK, msg=msg, END=Colors.NC))
        elif state.upper() == 'WARN':
            print(prompt.format(COL=Colors.WARN, msg=msg, END=Colors.NC))
        elif state.upper() == 'ERR':
            print(prompt.format(COL=Colors.ERR, msg=msg, END=Colors.NC))
        elif state.upper() == 'IMP':
            print(prompt.format(COL=Colors.BOLD, msg=msg, END=Colors.NC))

        if self.gui_console is not None:
            self.gui_console(msg)

    #####################################################
    #                    DevEnv METHODS                 #
    #####################################################
    def safe_core_list(self):
        return self.safe_mode_file_exception_list

    def simulator(self, prepare_only=False):
        self.console("[SIM] Clean sim workspace: {}".format(self.micros_sim_workspace))
        LocalMachine.FileHandler().remove(self.micros_sim_workspace, ignore=True)

        self.console("[SIM] Create workspace folder: {}".format(self.micros_sim_workspace))
        LocalMachine.FileHandler().create_dir(self.micros_sim_workspace)

        self.console("[SIM] Copy micrOS files to workdir")
        # Copy micrOS to sim workspace
        file_list = LocalMachine.FileHandler().list_dir(self.MicrOS_dir_path)
        for f in file_list:
            if f.endswith('.json'):
                continue
            f_path = os.path.join(self.MicrOS_dir_path, f)
            self.console("[SIM] Copy micrOS resources: {} -> {}".format(f_path, self.micros_sim_workspace))
            LocalMachine.FileHandler().copy(f_path, self.micros_sim_workspace)

        if prepare_only:
            # In case of automatic node_conf creation
            return

        workdir_handler = LocalMachine.SimplePopPushd()
        workdir_handler.pushd(self.micros_sim_workspace)

        # Import simulator resources
        self.console("[SIM] ADD simulator resources to python path")
        sys.path.append(self.micros_sim_resources)

        # Import simulator workspace
        self.console("[SIM] ADD micrOS workspace to python path")
        sys.path.append(self.micros_sim_workspace)

        try:
            self.console("[SIM] Start simulator: {}".format(self.micros_sim_workspace))
            import micrOSloader
        except Exception as e:
            print("[LOAD ERROR] micrOS SIM\n{}".format(e))
        try:
            micrOSloader.main()
        except Exception as e:
            print("[RUN ERROR] micrOS SIM\n{}".format(e))
        workdir_handler.popd()

    def exec_app(self, app_name, dev_name, app_postfix='_app'):
        print("=== NEW ===")
        app_name = "{}{}".format(app_name, app_postfix)
        import_cmd = "from {} import {}".format(".dashboard_apps", app_name)
        print("[APP] Import: {}".format(import_cmd))
        exec(import_cmd)
        print("[APP] Exec: {}.app(devfid='{}')".format(app_name, dev_name))
        return_value = eval("{}.app(devfid='{}')".format(app_name, dev_name))
        if return_value is not None:
            return return_value
        return ''

    def get_devices(self):
        self.console("------------------------------------------")
        self.console("-  LIST CONNECTED MICROS DEVICES VIA USB -", state='imp')
        self.console("------------------------------------------")
        micros_devices = []

        if self.dummy_exec:
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
                if "CP210" in str(item.description):
                    micros_devices.append(item.device)
                    self.console("Device was found: {}".format(item.device, state="imp"))
        # Eval device list, return with devices
        if len(micros_devices) > 0:
            self.console("Device was found. :)", state="ok")
        else:
            self.console("No device was connected. :(", state="err")
        return micros_devices

    def get_micropython_binaries(self):
        self.console("------------------------------------------")
        self.console("-         GET MICROPYTHON BINARIES       -", state='imp')
        self.console("------------------------------------------")
        micropython_bins_list = []

        mp_bin_list = [binary for binary in LocalMachine.FileHandler.list_dir(self.micropython_bin_dir_path) if
                       binary.endswith('.bin')]
        for mp_bin in mp_bin_list:
            micropython_bins_list.append(os.path.join(self.micropython_bin_dir_path, mp_bin))
        if len(micropython_bins_list) > 0:
            self.console("Micropython binary was found.", state='ok')
        else:
            self.console("Micropython binary was not found.", state='err')
        return micropython_bins_list

    #####################################################
    #             DevEnv EXTERNAL METHODS               #
    #####################################################
    def erase_dev(self):
        self.console("------------------------------------------")
        self.console("-           ERASE MICROS DEVICE          -", state='imp')
        self.console("------------------------------------------")
        self.__initialize_dev_env_for_deployment_vis_usb()

        selected_device = self.get_devices()[0]
        erase_cmd = self.dev_types_and_cmds[self.selected_device_type]['erase']
        print("selected_device_port: {}".format(selected_device))
        command = erase_cmd.format(dev=selected_device)
        self.console("CMD: {}".format(command))
        if self.dummy_exec:
            exitcode = 0
            stdout = "Dummy stdout"
        else:
            if 'esp32' in self.selected_device_type:
                self.console("[!!!] PRESS [EN] BUTTON TO ERASE DEVICE ...", state='imp')
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
        if exitcode == 0:
            self.console("Erase done.\n{}".format(stdout), state='ok')
            return True
        else:
            self.console("Erase failed.\n{} - {}".format(stdout, stderr), state='err')
            return False

    def deploy_micropython_dev(self):
        self.console("------------------------------------------")
        self.console("-            DEPLOY MICROPYTHON          -", state='imp')
        self.console("------------------------------------------")
        self.__initialize_dev_env_for_deployment_vis_usb()

        deploy_cmd = self.dev_types_and_cmds[self.selected_device_type]['deploy']
        selected_device = self.get_devices()[0]
        selected_micropython = self.selected_micropython_bin
        command = deploy_cmd.format(dev=selected_device, micropython=selected_micropython)
        self.console("CMD: {}".format(command))
        if self.dummy_exec:
            exitcode = 0
            stdout = "Dummy stdout"
        else:
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
        if exitcode == 0:
            self.console("Deployment done.\n{}".format(stdout), state='ok')
            time.sleep(1)
            return True
        else:
            self.console("Deployment failed.\n{} - {}".format(stdout, stderr), state='err')
            return False

    def __cleanup_precompiled_dir(self):
        for source in [pysource for pysource in LocalMachine.FileHandler.list_dir(self.precompiled_MicrOS_dir_path) \
                       if pysource.endswith('.py') or pysource.endswith('.mpy')]:
            to_remove_path = os.path.join(self.precompiled_MicrOS_dir_path, source)
            self.console("Cleanup dir - remove: {}".format(to_remove_path), state='imp')
            LocalMachine.FileHandler.remove(to_remove_path)

    def precompile_micros(self):
        self.console("------------------------------------------")
        self.console("-             PRECOMPILE MICROS          -", state='imp')
        self.console("------------------------------------------")

        # Skip precompile if mpy-cross not available
        if self.mpy_cross_compiler_path is None or not os.path.exists(self.mpy_cross_compiler_path):
            self.console("PRECOMPILE MICROS - FUNCTION NOT AVAILABLE - MPY-CROSS MISSING!", state='err')
            self.console("Use stored precompiled resources", state='ok')
            return False

        if not self.dummy_exec:
            self.__cleanup_precompiled_dir()

        file_prefix_blacklist = ['LM_', 'boot.py']
        tmp_precompile_set = set()
        tmp_skip_compile_set = set()
        error_cnt = 0
        # Filter source
        for source in [pysource for pysource in LocalMachine.FileHandler.list_dir(self.MicrOS_dir_path) if
                       pysource.endswith('.py')]:
            is_blacklisted = False
            for black_prefix in file_prefix_blacklist:
                if source.startswith(black_prefix) and source not in self.precompile_LM_wihitelist:
                    is_blacklisted = True
            if is_blacklisted:
                tmp_skip_compile_set.add(source)
            else:
                tmp_precompile_set.add(source)

        # Change workdir
        workdir_handler = LocalMachine.SimplePopPushd()
        workdir_handler.pushd(self.MicrOS_dir_path)

        # Execute based on filetered sets
        # |-> PRECOMPILE
        for to_compile in tmp_precompile_set:
            precompiled_target_name = to_compile.replace('.py', '.mpy')

            # Build micrOS with mpy-cross binary
            command = "{mpy_cross} {to_compile} -o {target_path}/{target_name} -v".format(
                mpy_cross=self.mpy_cross_compiler_path,
                to_compile=to_compile,
                target_path=self.precompiled_MicrOS_dir_path,
                target_name=precompiled_target_name)
            self.console("Precomile: {}\n|->CMD: {}".format(to_compile, command), state='imp')
            if not self.dummy_exec:
                exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
            else:
                exitcode = 0
                stderr = ''
            if exitcode == 0 and stderr == '':
                self.console("|---> DONE", state='ok')
            else:
                self.console("|---> ERROR: {} - {}".format(stdout, stderr), state='err')
                error_cnt += 1

        # Restore original workdir
        workdir_handler.popd()

        # |-> COPY
        for skip_compile in tmp_skip_compile_set:
            source_path = os.path.join(self.MicrOS_dir_path, skip_compile)
            self.console("SKIP precompile: {}".format(skip_compile), state='imp')
            if not self.dummy_exec:
                state = LocalMachine.FileHandler.copy(source_path, self.precompiled_MicrOS_dir_path)
            else:
                state = True
            if not state:
                self.console("Copy error", state='err')
                error_cnt += 1
        # Evaluation summary
        if error_cnt != 0:
            self.console("Some modules [{}] not compiled properly - please check the logs.".format(error_cnt))
            sys.exit(4)
        else:
            return True

    def __validate_json(self):
        is_valid = True
        local_config_path = os.path.join(self.precompiled_MicrOS_dir_path, 'node_config.json')
        try:
            if os.path.isfile(local_config_path):
                with open(local_config_path, 'r') as f:
                    text = f.read()
                    json.loads(text)
        except ValueError as e:
            self.console("Invalid config: {}\n{}".format(local_config_path, e))
            is_valid = False
        return is_valid

    def put_micros_to_dev(self):
        self.__initialize_dev_env_for_deployment_vis_usb()
        status = True
        config_is_valid = self.__validate_json()
        if not config_is_valid:
            sys.exit(6)

        ampy_cmd = self.dev_types_and_cmds[self.selected_device_type]['ampy_cmd']
        device = self.get_devices()[0]
        source_to_put_device = LocalMachine.FileHandler.list_dir(self.precompiled_MicrOS_dir_path)
        # Set source order - main, boot
        source_to_put_device.append(source_to_put_device.pop(source_to_put_device.index('boot.py')))

        # Change workdir
        workdir_handler = LocalMachine.SimplePopPushd()
        workdir_handler.pushd(self.precompiled_MicrOS_dir_path)

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

    def __safe_execute_ampy_cmd(self, command, source, retry=8):
        retry_orig = retry
        for retry in range(1, retry_orig):
            if not self.dummy_exec:
                try:
                    exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
                except Exception as e:
                    self.console(e)
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
        return status

    def connect_dev(self):
        self.__initialize_dev_env_for_deployment_vis_usb()
        self.console("WELCOME $USER - $(DATE)")
        self.console("TO EXIT: ctrl-a d OR ctrl-a ctrl-d")
        time.sleep(2)

        connect_cmd = self.dev_types_and_cmds[self.selected_device_type]['connect']
        selected_device = self.get_devices()[0]
        command = connect_cmd.format(dev=selected_device)
        self.console("CMD: {}".format(command))
        if not self.dummy_exec:
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
        self.disconnect_dev()

    def disconnect_dev(self):
        terminate_cmd = 'kill {pid}'
        command = terminate_cmd.format(pid=self.__dev_used_from())
        self.console("CMD: {}".format(command))
        if not self.dummy_exec:
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
        else:
            exitcode = 0
        self.console("Disconnect exitcode: {}".format(exitcode))

    def __dev_used_from(self):
        fuser_cmd = 'fuser {dev}'
        selected_device = self.get_devices()[0]
        command = fuser_cmd.format(dev=selected_device)
        self.console("CMD: {}".format(command))
        if self.dummy_exec:
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

    def update_micros_via_usb(self, force=False):
        self.__initialize_dev_env_for_deployment_vis_usb()
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

    def __get_node_config(self):
        ampy_cmd = self.dev_types_and_cmds[self.selected_device_type]['ampy_cmd']
        device = self.get_devices()[0]
        arguments = 'get node_config.json'
        command = ampy_cmd.format(dev=device, args=arguments)
        if not self.dummy_exec:
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
            self.archive_node_config()
        else:
            exitcode = 0
            stdout = '{"key": "Dummy stdout"}'
            stderr = ''
        if '\n' in stdout:
            stdout = stdout.strip().splitlines()
            stdout = str([line for line in stdout if '{' in line and '}' in line][0])
        return exitcode, stdout, stderr

    def __generate_default_config(self):
        self.console("GENERATE DEFAULT NODE_CONFIG.JSON")

        # Change workdir
        workdir_handler = LocalMachine.SimplePopPushd()
        workdir_handler.pushd(self.MicrOS_dir_path)

        create_default_config_command = "python3 ConfigHandler.py"
        if not self.dummy_exec:
            # Remove actual defualt config
            LocalMachine.FileHandler.remove(os.path.join(self.MicrOS_dir_path, 'node_config.json'))
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

    def backup_node_config(self):
        self.__initialize_dev_env_for_deployment_vis_usb()
        if len(self.get_devices()) > 0:
            exitcode, stdout, stderr = self.__get_node_config()
            print("1-: {}\n{}\n{}".format(exitcode, stdout, stderr))
            if exitcode == 0:
                self.console("Get Node config (node_config.json):")
                pprint.PrettyPrinter(indent=4).pprint(json.loads(stdout))
                state = self.__override_local_config_from_node(node_config=stdout)
                if state:
                    self.archive_node_config()
                    return True
        self.console("exitcode: {}\n{}\n{}".format(exitcode, stdout, stderr))
        return False

    def archive_node_config(self):
        self.console("ARCHIVE NODE_CONFIG.JSON")
        local_node_config = os.path.join(self.precompiled_MicrOS_dir_path, 'node_config.json')
        if os.path.isfile(local_node_config):
            with open(local_node_config, 'r') as f:
                node_devfid = json.load(f)['devfid']
            archive_node_config = os.path.join(self.MicrOS_node_config_archive,
                                               '{}-node_config.json'.format(node_devfid))
            LocalMachine.FileHandler.create_dir(self.MicrOS_node_config_archive)
            self.console("Archive node_config... to {}".format(archive_node_config))
            if not self.dummy_exec:
                LocalMachine.FileHandler.copy(local_node_config, archive_node_config)

    def restore_and_create_node_config(self):
        self.console("RESTORE NODE_CONFIG.JSON")
        self.__generate_default_config()
        conf_list = []
        index = -1
        if os.path.isdir(self.MicrOS_node_config_archive):
            conf_list = [conf for conf in LocalMachine.FileHandler.list_dir(self.MicrOS_node_config_archive) if
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
            target_path = os.path.join(self.precompiled_MicrOS_dir_path, selected_config.split('-')[1])
            source_path = os.path.join(self.MicrOS_node_config_archive, selected_config)
        elif selected_index == len(conf_list) - 1:
            # SKIP restore config - use the local version in mpy-micrOS folder
            target_path = os.path.join(self.precompiled_MicrOS_dir_path, 'node_config.json')
            source_path = None
        else:
            # Create new config - from micrOS folder path -> mpy-micrOS folder
            target_path = os.path.join(self.precompiled_MicrOS_dir_path, selected_config)
            source_path = os.path.join(self.MicrOS_dir_path, selected_config)
        self.console("Restore config: {} -> {}".format(source_path, target_path))
        if not self.dummy_exec:
            if source_path is not None:
                LocalMachine.FileHandler.copy(source_path, target_path)

        # In case of NEW config - profile injection option
        if selected_index == len(conf_list) - 2:
            # Inject profile data
            if self.inject_profile(target_path) is None:
                # Dump untouched config content
                with open(target_path, 'r') as f:
                    self.console(
                        "[ INFO ] Actual config:\n{}".format(json.dumps(json.load(f), indent=4, sort_keys=True)))

        # Manual config editing breakpoint
        self.console("=================== INFO =====================")
        self.console("[ INFO ] To edit your config, open: {}".format(target_path))
        input("[ QUESTION ] To continue, press enter.")
        # Dump config content
        with open(target_path, 'r') as f:
            self.console(
                "[ INFO ] Deployment with config:\n{}".format(json.dumps(json.load(f), indent=4, sort_keys=True)))

    def __override_local_config_from_node(self, node_config=None):
        node_config_path = os.path.join(self.precompiled_MicrOS_dir_path, 'node_config.json')
        self.console("Overwrite node_config.json with connected node config: {}".format(node_config_path), state='ok')
        if not self.dummy_exec and node_config is not None:
            with open(node_config_path, 'w') as f:
                f.write(node_config)
        return True

    def get_micrOS_version(self, config_string=None):
        # Get repo version
        version = self.get_micros_version_from_repo()
        # Get node version
        if not self.dummy_exec and config_string is not None:
            try:
                regex = r"\d+.\d+.\d+-\d+"
                version_on_node = re.findall(regex, config_string, re.MULTILINE)[0]
            except Exception as e:
                self.console("Obsolete node version - node version was not defined: {}".format(e), state='warn')
                version_on_node = 0
        else:
            version_on_node = "dummy version"
        return version, version_on_node

    def list_micros_filesystem(self):
        self.__initialize_dev_env_for_deployment_vis_usb()
        ampy_cmd = self.dev_types_and_cmds[self.selected_device_type]['ampy_cmd']
        device = self.get_devices()[0]
        command = ampy_cmd.format(dev=device, args='ls')
        if not self.dummy_exec:
            self.console("CMD: {}".format(command))
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
        else:
            exitcode = 0
            stdout = 'Dummy stdout'
        if exitcode == 0:
            self.console("micrOS node content:\n{}".format(stdout), state='ok')
        else:
            self.console("micrOS node content list error:\n{}".format(stderr), state='err')

    def micrOS_sim_default_conf_create(self):
        self.console("Create default micrOS node_config.json")
        # Prepare resources
        self.simulator(prepare_only=True)

        workdir_handler = LocalMachine.SimplePopPushd()
        workdir_handler.pushd(self.micros_sim_workspace)
        # Add sim workspace to python path
        sys.path.append(self.micros_sim_workspace)
        # Add sim libs for python path
        sys.path.append(self.micros_sim_resources)
        try:
            import ConfigHandler
        except Exception as e:
            self.console("[ERROR] micrOS SIM\n{}".format(e))
        workdir_handler.popd()

    def inject_profile(self, target_path):
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

    def LM_functions_static_dump_gen(self):
        """
        Generate static module-function provider json description: sfuncman.json
        [!] name dependency with micrOS internal manual provider
        """
        repo_version = self.get_micros_version_from_repo()
        static_help_json_path = os.path.join(self.sfuncman_output_path, 'sfuncman_{}.json'.format(repo_version))
        module_function_dict = {}
        for LM in (i.split('.')[0] for i in LocalMachine.FileHandler.list_dir(self.MicrOS_dir_path) if
                   i.startswith('LM_') and (i.endswith('.py'))):
            LMpath = '{}/{}.py'.format(self.MicrOS_dir_path, LM)
            try:
                module_int_name = LM.replace('LM_', '')
                module_function_dict[module_int_name] = []
                with open(LMpath, 'r') as f:
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        if 'def ' in line and 'def __' not in line:
                            if '(self' in line:
                                continue
                            # Gen proper func name
                            function_name = '{}'.format(line.split(')')[0]).replace("def", '').strip()
                            function_name = function_name.replace('(', ' ') \
                                .replace(',', '') \
                                .replace('msgobj=None', '') \
                                .replace('force=True', '')
                            # Save record
                            module_function_dict[module_int_name].append(function_name.strip())
            except Exception as e:
                self.console("STATIC micrOS HELP GEN: LM [{}] PARSER ERROR: {}".format(LM, e))
        self.console("Dump micrOS static manual: {}".format(static_help_json_path))
        with open(static_help_json_path, 'w') as f:
            json.dump(module_function_dict, f, indent=2)

    def purge_node_config_from_workdir(self):
        path = os.path.join(self.precompiled_MicrOS_dir_path, 'node_config.json')
        LocalMachine.FileHandler().remove(path, ignore=False)

    def deploy_micros(self, restore=True, purge_conf=False):
        """
        Clean board deployment with micropython + micrOS
        :param restore: restore and create node config
        :param purge_conf: purge node config - deletion
        :return: None
        """
        self.__initialize_dev_env_for_deployment_vis_usb()
        if purge_conf:
            self.purge_node_config_from_workdir()
        if restore:
            self.restore_and_create_node_config()
        if self.erase_dev():
            time.sleep(2)
            if self.deploy_micropython_dev():
                time.sleep(2)
                self.precompile_micros()
                time.sleep(2)
                self.put_micros_to_dev()
                self.archive_node_config()
            else:
                self.console("Deploy micropython error", state='err')
                self.execution_verdict.append("[ERROR] usb_deploy - micropython install failed")
        else:
            self.console("Erase device error", state='err')
        self.execution_verdict.append("[OK] usb_deploy was finished")

    def __clone_webrepl_repo(self):
        if os.path.isdir(os.path.dirname(self.webreplcli_repo_path)) and os.path.isfile(self.webreplcli_repo_path):
            return True
        # Download webrepl repo if necessary
        if not os.path.isfile(self.webreplcli_repo_path):
            # Change workdir
            workdir_handler = LocalMachine.SimplePopPushd()
            workdir_handler.pushd(os.path.dirname(os.path.dirname(self.webreplcli_repo_path)))

            command = 'git clone {url} {name}'.format(
                name='webrepl',
                url='https://github.com/micropython/webrepl.git')
            self.console("Clone webrepl repo: {}".format(command))
            if not self.dummy_exec:
                exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
            else:
                exitcode = 0
                stderr = ''

            # Restore workdir
            workdir_handler.popd()
            if exitcode == 0:
                self.console("\tClone {}DONE{}".format(Colors.OK, Colors.NC))
            else:
                self.console(
                    "GIT CLONE {}ERROR{}:\nstdout: {}\nstderr: {}".format(Colors.ERR, Colors.NC, stdout, stderr))
                return False
        return True

    def get_micros_version_from_repo(self):
        # Get repo version
        with open(os.path.join(self.MicrOS_dir_path, 'SocketServer.py'), 'r') as f:
            code_lines_string = f.read()
        regex = r"\d+.\d+.\d+-\d+"
        repo_version = re.findall(regex, code_lines_string, re.MULTILINE)[0]
        return repo_version

    def update_with_webrepl(self, force=False, device=None, lm_only=False, loader_update=False, ota_password='ADmin123'):
        """
        OTA UPDATE via webrepl
            git clone https://github.com/micropython/webrepl.git
            info: https://techoverflow.net/2020/02/22/how-to-upload-files-to-micropython-using-webrepl-using-webrepl_cli-py/
            ./webrepl/webrepl_cli.py -p <password> <input_file> espressif.local:<output_file>
        """
        print("OTA UPDATE")
        upload_path_list = []

        def __version_compare(repo_version, fuid):
            """
            version SemVer: 1.2.3-4 - major[1.2]minor[.3]patch[-4]
                In case of [major] change force full update (micrOS safe core: micrOSloadoer, etc.)
                In case of [minor + patch] change install main micrOS resources + LMs
            :param fud: friendly unique id / unique id
            :return: repo_version, device_version, force
            """
            # Get device version via socket
            status, answer_msg = socketClient.run(['--dev', fuid, 'version'])
            device_version = answer_msg.strip() if status else None
            # Parse versions
            repo_major_version = repo_version.split('.')[0:2]
            device_major_version = device_version.split('.')[0:2] if device_version is not None and len(
                device_version.split('.')) == 3 else device_version
            force = False if repo_major_version == device_major_version else True
            return repo_version, device_version, force

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

        # Get versions: micrOS repo + live device, compare versions
        repo_version, device_version, auto_force = __version_compare(self.get_micros_version_from_repo(), fuid)

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
        resource_list_to_upload = [os.path.join(self.precompiled_MicrOS_dir_path, pysource) for pysource in
                                   LocalMachine.FileHandler.list_dir(self.precompiled_MicrOS_dir_path)
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

        def enable_micros_ota_update_via_webrepl(dev=None):
            # Get specific device from device list
            self.console("Select device to update ...", state='IMP')
            socketClient.ConnectionData.read_micrOS_device_cache()
            # Get device IP and friendly name
            if dev is None:
                # Select device dynamically - cmdline
                self.console("Select device manually:")
                device_ip, port, fuid, uid = socketClient.ConnectionData.select_device()
            else:
                # Select device from code / gui
                self.console("Device was selected with func param: {}".format(dev))
                device_ip, fuid = device[1], device[0]
            self.console("\tDevice was selected (fuid, ip): {} -> {}".format(fuid, device_ip), state='OK')
            self.console(" \tWebRepl OTA password: {}".format(ota_password), state='OK')

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
                    if self.dummy_exec:
                        status, answer_msg = True, 'dummy exec'
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

        def __lock_handler(host, ota_password, lock=False):
            """
            [1] Create .if_mode file (local file system)
                lock: True -> value: webrepl
                lock: False -> value: micros
            [2] Copy file to device
            """

            webrepl_if_mode = 'webrepl'  # micrOS system runs in webrepl mode - no micrOS interface running
            micros_if_mode = 'micros'  # micrOS running in normal mode - micrOS interface is active
            state = False
            lock_value = webrepl_if_mode if lock else micros_if_mode  # Select lock value
            # Create webrepl copy command
            command = 'python {api} -p {pwd} .if_mode {host}:.if_mode'.format(api=self.webreplcli_repo_path,
                                                                              pwd=ota_password,
                                                                              host=host)

            workdir_handler = LocalMachine.SimplePopPushd()
            workdir_handler.pushd(self.precompiled_MicrOS_dir_path)

            # Create / modify file
            with open(".if_mode", 'w') as f:
                f.write(lock_value)

            # Wait for device reboot
            if lock:
                for i in range(1, 7):
                    self.console("\tWait for device: {}/6 sec".format(i))
                    time.sleep(1)

            if self.dummy_exec:
                self.console("Webrepl CMD: {}".format(command))
                return True
            else:
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
                    state = False
                except Exception as e:
                    self.console("Create lock/unlock failed: {}".format(e))
                    state = False
                self.console("[ERROR] Create lock/unlock failed")
                # Cleanup lock file: .if_mode + restore path
                LocalMachine.FileHandler.remove('.if_mode', ignore=True)
                workdir_handler.popd()
            return state

        def wait_for_micrOS_up_again():
            self.console("Device will reboot automatically, please wait 4-8 seconds.")
            time.sleep(4)
            up_again_status = False
            for is_up_again in range(0, 10):
                self.console("[{}/10] Try to connect ...".format(is_up_again))
                status, answer_msg = socketClient.run(['--dev', fuid, 'hello'])
                if status:
                    self.console("Device {} is up again".format(fuid), state='OK')
                    up_again_status = True
                    break
                if not up_again_status:
                    time.sleep(2)

            # Print manual steps if necessary
            if not up_again_status:
                self.console("Auto restart timeout, please reboot device manually.", state='WARN')
                self.console("Please reset your device.", state='IMP')
                self.console("\t[1]HINT: open in browser: http://micropython.org/webrepl/#{}:8266/".format(device_ip))
                self.console("\t[2]HINT: log in and execute: import reset")
                self.console("\t[3]HINT: OR skip [2] point and reset manually")
                self.execution_verdict.append(
                    "[WARN] ota_update - device auto restart failed,\nplease reset the device manually.")
            self.execution_verdict.append("[OK] ota_update was finished")
            return up_again_status

        # -------------------------- main --------------------------- #

        # GET webrepl repo
        if not self.__clone_webrepl_repo():
            self.console("Webrepl repo not available...", state='ERR')
            self.execution_verdict.append("[ERR] ota_update - clone webrepl repo")
            return False

        self.console("MICROS SOCKET WON'T BE AVAILABLE UNDER UPDATE.")

        # Enable micrOS OTA mode
        status, device_ip, fuid = enable_micros_ota_update_via_webrepl(dev=device)

        # Create lock file for ota update
        self.console("[UPLOAD] Copy files to device...", state='IMP')
        self.console("\t[!] Create update lock (webrepl bootup) under OTA update", state='IMP')
        if not __lock_handler(host=device_ip, ota_password=ota_password, lock=True):
            self.console("OTA lock creation failed", state='ERR')
            self.execution_verdict.append("[ERR] ota_update - OTA update locked creation failed")
            return False

        # Upload path list
        for index, source in enumerate(upload_path_list):
            # calculate progress
            progress = round(((index + 1) / len(upload_path_list)) * 100)

            # Check no space in the file name
            if ' ' in source:
                self.console("\t[{}%][SKIP UPLOAD] space in resource name ... {}".format(progress, source),
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

            command = 'python {api} -p {pwd} {input_file} {host}:{target_path}'.format(
                api=self.webreplcli_repo_path, pwd=ota_password,
                input_file=source_name, host=device_ip,
                target_path=source_name_target)

            for ret_cnt in range(0, 5):
                self.console(
                    "[{}%] {} copy over webrepl {}:{}".format(progress, source_name, device_ip, source_name_target))
                if self.dummy_exec:
                    self.console("[{}%][UPLOAD] Webrepl CMD: {}".format(progress, command))
                    exitcode = 0
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
        if __lock_handler(host=device_ip, ota_password=ota_password, lock=False):
            self.console("\tOTA UPDATE WAS SUCCESSFUL", state='OK')
        else:
            self.console("\tOTA UPDATE WAS FAILED, PLEASE TRY AGAIN.", state='ERR')
            self.execution_verdict.append("[WARN] ota_update - failed to remove OTA update lock")
        return wait_for_micrOS_up_again()


if __name__ == "__main__":
    d = MicrOSDevTool()
    d.LM_functions_static_dump_gen()
