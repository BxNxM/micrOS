#!/usr/bin/env python3

import LocalMachine
from TerminalColors import Colors
import os
import sys
import time
MYPATH = os.path.dirname(os.path.abspath(__file__))

class MicrOSDevTool():

    def __init__(self, dummy_exec=False):
        self.dummy_exec = dummy_exec
        self.deployment_app_dependences = ['ampy', 'esptool.py']
        self.nodemcu_device_subnames = ['SLAB_USBtoUART', 'USB0']
        self.selected_device_type = 'esp8266'
        self.mpy_cross_compiler_path = os.path.join(MYPATH, '../../micropython_repo/micropython/mpy-cross/mpy-cross')
        self.dev_types_and_cmds = \
                {'esp8266': \
                   {'erase': 'esptool.py --port {dev} erase_flash', \
                    'deploy': 'esptool.py --port {dev} --baud 460800 write_flash --flash_size=detect -fm dio 0 {micropython}', \
                    'connect': 'screen {dev} 115200',
                    'ampy_cmd': 'ampy -p {dev} -b 115200 {args}'} \
                }

        # DevEnv base pathes
        self.MicrOS_dir_path = os.path.join(MYPATH, "../../MicrOS")
        self.precompiled_MicrOS_dir_path = os.path.join(MYPATH, "../../mpy-MicrOS")
        self.micropython_bin_dir_path = os.path.join(MYPATH, "../../framework")

        # Filled by methods
        self.micropython_bins_list = []
        self.micros_devices = []
        self.index_of_sected_micropython_bin = 0
        self.index_of_selected_device = 0

        # Initialize DevEnv - find micropython binaries, device
        self.__initialize_dev_env()

    #####################################################
    #               BASE / INTERNAL METHODS             #
    #####################################################
    def __initialize_dev_env(self):
        # Check dependences method
        state = self.deployment_dependence_handling()
        if state:
            # Find micropython binaries
            mp_bins = self.get_micropython_binaries()
            # Find MicrOS devices
            devices = self.get_devices()
            if len(mp_bins) > 0 and len(devices) > 0:
                self.console("Micropython binary and device was found.", state='ok')
                self.__select_device_and_micropython()
            else:
                self.console("Micropython binary and/or device missing!\nBINS: {}\nDEV: {}".format(mp_bins, devices), state='err')
                #sys.exit(2)
        else:
            self.console("Please install the dependences: {}".format(self.deployment_app_dependences), state='err')
            sys.exit(1)

    def __select_device_and_micropython(self):
        # Select micropython TODO
        if len(self.micropython_bins_list) > 1:
            # set self.index_of_sected_micropython_bin
            pass

        # Select device TODO
        if len(self.micros_devices) > 1:
            # set self.index_of_selected_device
            pass

    def __get_device(self):
        if not self.dummy_exec:
            return self.micros_devices[self.index_of_selected_device]
        else:
            return "dummy_device"

    def __get_micropython(self):
        return self.micropython_bins_list[self.index_of_sected_micropython_bin]

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

    #####################################################
    #                    DevEnv METHODS                 #
    #####################################################
    def deployment_dependence_handling(self):
        self.console("------------------------------------------")
        self.console("-      CHECK THE DEV ENV DEPENDENCES     -", state='imp')
        self.console("------------------------------------------")

        dep_ok = True
        for appdep in self.deployment_app_dependences:
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command("{} --help".format(appdep), shell=True)
            if exitcode == 0:
                self.console("[DEPENDENCY] {} available.".format(appdep), state='ok')
            else:
                self.console("[DEPENDENCY] {} NOT available.".format(appdep), state='err')
                dep_ok = False
                # TODO: install?
        return dep_ok

    def get_devices(self):
        self.console("------------------------------------------")
        self.console("-  LIST CONNECTED MICROS DEVICES VIA USB -", state='imp')
        self.console("------------------------------------------")
        self.micros_devices = []

        dev_path = '/dev/'
        content_list = [ dev for dev in LocalMachine.FileHandler.list_dir(dev_path) if "tty" in dev ]
        for present_dev in content_list:
            for dev_identifier in self.nodemcu_device_subnames:
                if dev_identifier in present_dev:
                    dev_abs_path = os.path.join(dev_path, present_dev)
                    self.micros_devices.append(dev_abs_path)
                    self.console("Device was found: {}".format(dev_abs_path), state="imp")
                    break
        if len(self.micros_devices) > 0:
            self.console("Device was found. :)", state="ok")
        else:
            self.console("No device was connected. :(", state="err")
        return self.micros_devices

    def get_micropython_binaries(self):
        self.console("------------------------------------------")
        self.console("-         GET MICROPYTHON BINARIES       -", state='imp')
        self.console("------------------------------------------")
        self.micropython_bins_list = []

        mp_bin_list = [ binary for binary in LocalMachine.FileHandler.list_dir(self.micropython_bin_dir_path) if binary.endswith('.bin') ]
        for mp_bin in mp_bin_list:
            self.micropython_bins_list.append(os.path.join(self.micropython_bin_dir_path, mp_bin))
        if len(self.micropython_bins_list) > 0:
            self.console("Micropython binary was found.", state='ok')
        else:
            self.console("Micropython binary was not found.", state='err')
        return self.micropython_bins_list

    #####################################################
    #             DevEnv EXTERNAL METHODS               #
    #####################################################
    def erase_dev(self):
        self.console("------------------------------------------")
        self.console("-           ERASE MICROS DEVICE          -", state='imp')
        self.console("------------------------------------------")

        erase_cmd = self.dev_types_and_cmds[self.selected_device_type]['erase']
        selected_device = self.__get_device()
        command = erase_cmd.format(dev=selected_device)
        self.console("CMD: {}".format(command))
        if self.dummy_exec:
            exitcode = 0
            stdout = "Dummy stdout"
        else:
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

        deploy_cmd = self.dev_types_and_cmds[self.selected_device_type]['deploy']
        selected_device = self.__get_device()
        selected_micropython = self.__get_micropython()
        command = deploy_cmd.format(dev=selected_device, micropython=selected_micropython)
        self.console("CMD: {}".format(command))
        if self.dummy_exec:
            exitcode = 0
            stdout = "Dummy stdout"
        else:
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
        if exitcode == 0:
            self.console("Deployment done.\n{}".format(stdout), state='ok')
            return True
        else:
            self.console("Deployment failed.\n{} - {}".format(stdout, stderr), state='err')
            return False

    def __clone_micropython_repo(self):
        command = 'git clone https://github.com/micropython/micropython.git'
        # TODO: [1] check micropython repo path - CLONE if not exists / update
        #       [2] check path: self.mpy_cross_compiler_path - make if not exists

    def __cleanup_precompiled_dir(self):
        for source in [ pysource for pysource in LocalMachine.FileHandler.list_dir(self.precompiled_MicrOS_dir_path) \
                        if pysource.endswith('.py') or pysource.endswith('.mpy') ]:
            to_remove_path = os.path.join(self.precompiled_MicrOS_dir_path, source)
            self.console("Cleanup dir - remove: {}".format(to_remove_path), state='imp')
            LocalMachine.FileHandler.remove(to_remove_path)

    def precompile_micros(self):
        self.console("------------------------------------------")
        self.console("-            DEPLOY MICROPYTHON          -", state='imp')
        self.console("------------------------------------------")

        if not self.dummy_exec:
            self.__cleanup_precompiled_dir()

        file_prefix_blacklist = ['LM_', 'main.py', 'boot.py']
        tmp_precompile_set = set()
        tmp_skip_compile_set = set()
        error_cnt = 0
        # Filter source
        for source in [ pysource for pysource in LocalMachine.FileHandler.list_dir(self.MicrOS_dir_path) if pysource.endswith('.py') ]:
            is_blacklisted = False
            for black_prefix in file_prefix_blacklist:
                if source.startswith(black_prefix):
                    is_blacklisted = True
            if is_blacklisted:
                tmp_skip_compile_set.add(source)
            else:
                tmp_precompile_set.add(source)
        # Execute based on filetered sets
        # |-> PRECOMPILE
        for to_compile in tmp_precompile_set:
            source_path = os.path.join(self.MicrOS_dir_path, to_compile)
            precompiled_target_name = to_compile.replace('.py', '.mpy')
            command = "{mpy_cross} {to_compile} -o {target_path}/{target_name} -v".format(mpy_cross=self.mpy_cross_compiler_path, \
                                                                                          to_compile=source_path, \
                                                                                          target_path=self.precompiled_MicrOS_dir_path, \
                                                                                          target_name=precompiled_target_name)
            self.console("Precomile: {}\n|->CMD: {}".format(to_compile, command), state='imp')
            if not self.dummy_exec:
                exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
            else:
                exitcode = 0
            if exitcode == 0:
                self.console("|---> DONE", state='ok')
            else:
                self.console("|---> ERROR: {} - {}".format(stdout, stderr), state='err')
                error_cnt+=1

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

    def put_micros_to_dev(self):
        ampy_cmd = erase_cmd = self.dev_types_and_cmds[self.selected_device_type]['ampy_cmd']
        device = self.__get_device()
        for source in LocalMachine.FileHandler.list_dir(self.precompiled_MicrOS_dir_path):
            source_path = os.path.join(self.precompiled_MicrOS_dir_path, source)
            ampy_args = 'put {from_} {to}'.format(from_=source_path, to=os.path.basename(source))
            command = ampy_cmd.format(dev=device, args=ampy_args)
            print("Put {} -> {}".format(source_path, '{}/{}'.format(device, os.path.basename(source))))
            print("CMD: {}".format(command))
            if not self.dummy_exec:
                exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
            else:
                exitcode = 0
            if exitcode == 0:
                self.console("|-> OK", state='ok')
            else:
                self.console("|-> ERROR", state='err')
                sys.exit(5)
        return True

    def connect_dev(self):
        self.console("WELCOME $USER - $(DATE)")
        self.console("TO EXIT: ctrl-a d OR ctrl-a ctrl-d")
        time.sleep(2)

        connect_cmd = self.dev_types_and_cmds[self.selected_device_type]['connect']
        selected_device = self.__get_device()
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
        selected_device = self.__get_device()
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

    def update_micros_via_usb(self):
        ampy_cmd = erase_cmd = self.dev_types_and_cmds[self.selected_device_type]['ampy_cmd']
        device = self.__get_device()
        arguments = 'get node_config.json'
        command = ampy_cmd.format(dev=device, args=arguments)
        if not self.dummy_exec:
            exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)
        else:
            exitcode = 0
            stdout = 'Dummy stdout'
        if exitcode == 0:
            self.console("Get Node config (node_config.json)\n{}".format(stdout))
            # TODO: save config + redeploy
        else:
            self.console("Node config error: {} - {}".format(stdout, stderr))

    def get_micrOS_version(self):
        code_version_var_name = 'self.socket_interpreter_version'
        # Get MicrOS local repo version
        micros_version_module = os.path.join(self.MicrOS_dir_path, 'SocketServer.py')
        with open(micros_version_module, 'r') as f:
            code_lines = f.read().split('\n')
        versions = [ line.strip().split('=')[1] for line in code_lines if line.strip().startswith(code_version_var_name) ]
        version = versions[0].strip()
        # TODO: get micros version on node...
        return version, ""

    def deploy_micros(self):
        self.erase_dev()
        time.sleep(1)
        self.deploy_micropython_dev()
        time.sleep(1)
        self.precompile_micros()
        self.put_micros_to_dev()

if __name__ == "__main__":
    d = MicrOSDevTool()
    d.erase_dev()
