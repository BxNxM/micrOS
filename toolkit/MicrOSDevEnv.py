#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import importlib

MYPATH = os.path.dirname(__file__)
print("Module [MicrOSDevEnv] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYPATH))

try:
    from .DevEnvOTA import OTA
    from .DevEnvUSB import USB
    from .DevEnvCompile import Compile
    from .micrOSDocGen import MicrOSDocGen
    from .lib import LocalMachine
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    from DevEnvOTA import OTA
    from DevEnvUSB import USB
    from DevEnvCompile import Compile
    from micrOSDocGen import MicrOSDocGen
    from lib import LocalMachine


class MicrOSDevTool(MicrOSDocGen, OTA, USB):

    def __init__(self, dummy_exec=False, gui_console=None, cmdgui=True):
        self.dummy_exec = dummy_exec
        OTA.__init__(self, cmdgui=cmdgui, gui_console=gui_console, dry_run=dummy_exec)
        USB.__init__(self, dry_run=dummy_exec)
        # handle space in path: command line "escape path fix"
        self.micros_sim_resources = os.path.join(MYPATH, 'simulator_lib')
        self.init_doc_gen_paths()

    #####################################################
    #                    DevEnv METHODS                 #
    #####################################################
    def precompile_micros(self, cleanup=True):
        micros_dev_env = Compile().is_mpycross_available()
        if not micros_dev_env:
            self.console("SKIP PRECOMPILE - DEV ENV INACTIVE\n\t-> mpy-cross not available", state='warn')
            return True
        self.console("PRECOMPILE - DEV ENV ACTIVE: mpy-cross available", state='ok')
        state = super(MicrOSDevTool, self).precompile_micros(cleanup)
        # Drops Segmentation fault: 11 error: simulator doc gen... TODO
        self.LM_functions_static_dump_gen()
        return state

    def simulator(self, prepare_only=False, stop=False, restart=False):          # <<<<------ SIM hack here... (default: False)
        if (not stop or prepare_only) and not restart:
            ######################  Preparation phase  ######################
            self.console("[SIM] Clean sim workspace: {}".format(self.micros_sim_workspace))
            LocalMachine.FileHandler().remove(self.micros_sim_workspace, ignore=True)

            self.console("[SIM] Create workspace folder: {}".format(self.micros_sim_workspace))
            LocalMachine.FileHandler().create_dir(self.micros_sim_workspace)

            self.console("[SIM] Copy micrOS files to workdir")
            # Copy micrOS to sim workspace
            file_list = LocalMachine.FileHandler().list_dir(self.micrOS_dir_path)
            for f in file_list:
                if f.endswith('.json'):
                    continue
                f_path = os.path.join(self.micrOS_dir_path, f)
                if f.startswith("_") or f.startswith("."):
                    # SKIP files startswith `_` and `.`
                    continue
                _, f_type = LocalMachine.FileHandler.path_is_exists(f_path)
                target_dir = self.micros_sim_workspace
                if f_type == "d":
                    target_dir = os.path.join(self.micros_sim_workspace, f)
                self.console(f"[SIM] Copy micrOS resources: {f_path} -> {target_dir}")
                if not LocalMachine.FileHandler().copy(f_path, target_dir):
                    self.console(f"[ERROR] Failed to copy: {f_path}")

            if prepare_only:
                # In case of automatic node_conf creation
                return

        ######################  Execution phase  ######################

        # Import simulator resources - magic
        self.console("[SIM] ADD simulator resources to python path")
        sys.path.append(self.micros_sim_resources)
        import simulator

        sim_proc = simulator.micrOSIM()
        if stop:
            try:
                sim_proc.stop_all()
            except Exception as e:
                print(e)
            if stop:
                return
        # Start micrOS on host
        sim_proc.start()
        return sim_proc

    def exec_app(self, app_name, dev_name, password=None):
        print("=== NEW ===")
        module_root = f"{__package__}.dashboard_apps" if __package__ else "dashboard_apps"
        module_path = f"{module_root}.{app_name}"
        print("[APP] Import: {}".format(module_path))
        module = importlib.import_module(module_path)
        app_entry = getattr(module, 'app')
        if password is None:
            print(f"[APP] Exec: {app_name}.app(devfid='{dev_name}')")
            return_value = app_entry(devfid=dev_name)
        else:
            try:
                print(f"[APP] Exec: {app_name}.app(devfid='{dev_name}', pwd='******')")
                return_value = app_entry(devfid=dev_name, pwd=password)
            except TypeError as e:
                print(f"[APP] Exec: {app_name}.app(devfid='{dev_name}') password error: {e}\nRETRY")
                return_value = app_entry(devfid=dev_name)
        if return_value is not None:
            return return_value
        return ''

    #####################################################
    #             DevEnv EXTERNAL METHODS               #
    #####################################################

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


if __name__ == "__main__":
    d = MicrOSDevTool()
    d.LM_functions_static_dump_gen()
