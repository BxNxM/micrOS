import os
import sys
import re

MYPATH = os.path.dirname(__file__)
print("Module [DevEnvBase] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYPATH))

try:
    from .lib import LocalMachine
    from .lib.TerminalColors import Colors
    from .lib.file_extensions import check_all_extensions, check_web_extensions
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    from lib import LocalMachine
    from lib.TerminalColors import Colors
    from lib.file_extensions import check_all_extensions, check_web_extensions

try:
    import mpy_cross
    print("{}MICROPYTHON mpy_cross version{}:".format(Colors.WARN, Colors.NC))
    print("{}|_ To update mpy_cross{}: source magic.bash env; pip uninstall mpy_cross; pip install mpy_cross".format(
        Colors.WARN, Colors.NC))
    MPY_IS_V6 = False
except Exception as e:
    print("{}[!!!] mpy_cross error{}: {}".format(Colors.ERR, Colors.NC, e))
    mpy_cross = None

if mpy_cross is None:
    try:
        import mpy_cross_v6
        mpy_cross = mpy_cross_v6
        print("{}MICROPYTHON mpy_cross version{}:".format(Colors.WARN, Colors.NC))
        print("{}|_ To update mpy_cross-v6{}: source magic.bash env; pip uninstall mpy_cross_v6; pip install mpy_cross_v6".format(
            Colors.WARN, Colors.NC))
        MPY_IS_V6 = True
    except Exception as e:
        print("{}[!!!] mpy_cross_v6 error{}: {}".format(Colors.ERR, Colors.NC, e))
        mpy_cross = None


class Compile:

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.micrOS_dir_path = os.path.join(MYPATH, "../micrOS/source")
        self.precompiled_micrOS_dir_path = os.path.join(MYPATH, "workspace/precompiled")
        self.precompiled_micrOS_version_path = os.path.join(MYPATH, "workspace/precompiled/_mpy.version")
        self.sfuncman_output_path = os.path.join(MYPATH, "../micrOS/client/sfuncman/")
        self.precompile_LM_whitelist = self._read_LMs_whitelist()
        self.python_interpreter = sys.executable
        self.micros_sim_workspace = os.path.join(MYPATH, 'workspace/simulator')
        self.execution_verdict = []
        # mpy-cross binary path for cross compilation
        if mpy_cross is None:
            self.mpy_cross_compiler_path = None
        else:
            if MPY_IS_V6:
                # Store mpy_cross_V6 executable path
                self.mpy_cross_compiler_path = str(mpy_cross.MPY_CROSS_PATH)
            else:
                # Store mpy_cross executable path
                self.mpy_cross_compiler_path = mpy_cross.mpy_cross


    @staticmethod
    def is_mpycross_available():
        return False if mpy_cross is None else True

    @property
    def precompiled_mpy_cross_version(self):
        """ GET STORED MPY-CROSS VERSION UNDER PRECOMPILED DIR"""
        mpy_version = None
        try:
            with open(self.precompiled_micrOS_version_path, 'r') as f:
                mpy_version = f.read().strip()
            self.console(f"LOAD MPY-CROSS VERSION: {mpy_version}", state="OK")
        except Exception as e:
            self.console(f"LOAD MPY-CROSS VERSION ERROR: {e}", state='ERR')
        return mpy_version

    def _save_precompiled_mpy_cross_version(self):
        """ STORE MPY-CROSS VERSION UNDER PRECOMPILED DIR"""
        if self.is_mpycross_available():
            self.console(f"SAVE MPY-CROSS VERSION: {self.precompiled_micrOS_version_path} ({self.mpy_cross_compiler_path})")
            command = "{mpy_cross} --version".format(mpy_cross=self.mpy_cross_compiler_path)
            result = LocalMachine.CommandHandler.run_command(command, shell=True)
            exitcode = result[0]
            raw_version = result[1]
            if exitcode == 0 and isinstance(raw_version, str):
                try:
                    version = [v for v in raw_version.lower().split(" ") if v.startswith('v')][0]
                    mpy_cross_version = version.split('-')[0].replace('v', '')
                    with open(self.precompiled_micrOS_version_path, 'w') as f:
                        f.write(mpy_cross_version)
                    self.console(f"\t\tmpy-cross version was successfully saved ({mpy_cross_version}) to: {self.precompiled_micrOS_version_path}", state='OK')
                except Exception as e:
                    self.console(f"Cannot get mpy-cross version: {e}", state="ERR")
        else:
            self.console(f"Cannot save mpy-cross version: {self.precompiled_micrOS_version_path}", state='ERR')

    @staticmethod
    def _read_LMs_whitelist():
        lm_to_compile_conf_path = os.path.join(MYPATH, "LM_to_compile.dat")
        whitelist = []
        if os.path.isfile(lm_to_compile_conf_path):
            with open(lm_to_compile_conf_path, 'r') as f:
                whitelist = [str(k.strip()) for k in f.read().strip().split() if
                             k.strip().startswith('LM_') and k.strip().endswith('.py')]
        return whitelist

    @staticmethod
    def console(msg, state=None):
        """
        Console print with highlights
        - None: use no highlights
        - OK: ok - green
        - WARN: warning - yellow
        - ERR: error - red
        - IMP: important - bold
        """
        prompt = "{COL}[micrOS]{END} {msg}"
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

    def __cleanup_precompiled_dir(self):
        self.console("Delete precompiled components: {}".format(self.precompiled_micrOS_dir_path))
        for source in [pysource for pysource in LocalMachine.FileHandler.list_dir(self.precompiled_micrOS_dir_path)
                       if check_all_extensions(pysource)]:
            to_remove_path = os.path.join(self.precompiled_micrOS_dir_path, source)
            self.console("\t|-remove: {}".format(to_remove_path), state='imp')
            if not self.dry_run:
                LocalMachine.FileHandler.remove(to_remove_path)

    def get_micros_version_from_repo(self):
        # Get repo version
        with open(os.path.join(self.micrOS_dir_path, 'Shell.py'), 'r') as f:
            code_lines_string = f.read()
        regex = r"\d+.\d+.\d+-\d+"
        repo_version = re.findall(regex, code_lines_string, re.MULTILINE)[0]
        return repo_version

    def precompile_micros(self):
        self.console("------------------------------------------")
        self.console("-             PRECOMPILE MICROS          -", state='imp')
        self.console("------------------------------------------")

        # Skip precompile if mpy-cross not available
        if self.mpy_cross_compiler_path is None or not os.path.exists(self.mpy_cross_compiler_path):
            self.console("PRECOMPILE MICROS - FUNCTION NOT AVAILABLE - MPY-CROSS MISSING!", state='err')
            self.console("Use stored precompiled resources", state='ok')
            return False

        self.__cleanup_precompiled_dir()

        file_prefix_blacklist = ['LM_', 'main.py', 'boot.py']
        tmp_precompile_set = set()
        tmp_skip_compile_set = set()
        error_cnt = 0
        # Filter component source
        for source in [pysource for pysource in LocalMachine.FileHandler.list_dir(self.micrOS_dir_path) if
                       pysource.endswith('.py')]:
            is_blacklisted = False
            for black_prefix in file_prefix_blacklist:
                if source.startswith(black_prefix) and source not in self.precompile_LM_whitelist:
                    is_blacklisted = True
            if is_blacklisted:
                tmp_skip_compile_set.add(source)
            else:
                tmp_precompile_set.add(source)

        # Change workdir
        workdir_handler = LocalMachine.SimplePopPushd()
        workdir_handler.pushd(self.micrOS_dir_path)

        # Execute based on filetered sets
        # |-> PRECOMPILE
        for to_compile in tmp_precompile_set:
            precompiled_target_name = to_compile.replace('.py', '.mpy')

            # Build micrOS with mpy-cross binary - handle space in path
            command = "{mpy_cross} {to_compile} -o {target_path}/{target_name} -v".format(
                mpy_cross=self.mpy_cross_compiler_path.replace(' ', os.sep),
                to_compile=to_compile,
                target_path=self.precompiled_micrOS_dir_path.replace(' ', os.sep),
                target_name=precompiled_target_name)
            if self.dry_run:
                exitcode, stdout, stderr = 0, 'dry-run', ''
            else:
                exitcode, stdout, stderr = LocalMachine.CommandHandler.run_command(command, shell=True)

            verdict = "Precompiled{}: {}\n|-> {}"
            if exitcode == 0 and stderr == '':
                self.console(verdict.format('', to_compile, command), state='ok')
            else:
                self.console(verdict.format(' FAILED', to_compile, command), state='err')
                self.console("|---> {} - {}".format(stdout, stderr), state='err')
                error_cnt += 1

        # Restore original workdir
        workdir_handler.popd()

        # |-> COPY
        for skip_compile in tmp_skip_compile_set:
            source_path = os.path.join(self.micrOS_dir_path, skip_compile)
            self.console("SKIP precompile: {}".format(skip_compile), state='ok')
            if self.dry_run:
                state = True
            else:
                state = LocalMachine.FileHandler.copy(source_path, self.precompiled_micrOS_dir_path)
            if not state:
                self.console("Copy error", state='err')
                error_cnt += 1
        self.copy_other_resources_to_precompiled()
        self._save_precompiled_mpy_cross_version()
        # Evaluation summary
        if error_cnt != 0:
            self.console("Some modules [{}] not compiled properly - please check the logs.".format(error_cnt),
                         state='err')
            sys.exit(4)
        else:
            return True

    def copy_other_resources_to_precompiled(self):
        """micrOS resource formats to copy to board: html"""
        # Change workdir
        workdir_handler = LocalMachine.SimplePopPushd()
        workdir_handler.pushd(self.micrOS_dir_path)

        self.console("COPY additional resources")
        # Filter component source
        for source in [pysource for pysource in LocalMachine.FileHandler.list_dir(self.micrOS_dir_path) if
                       check_web_extensions(pysource)]:
            source_path = os.path.join(self.micrOS_dir_path, source)
            if self.dry_run:
                state = True
            else:
                state = LocalMachine.FileHandler.copy(source_path, self.precompiled_micrOS_dir_path)
            if not state:
                self.console("Copy error", state='err')
        workdir_handler.popd()


    def get_micrOS_version(self, config_string=None):
        # Get repo version
        version = self.get_micros_version_from_repo()
        # Get node version
        if not self.dry_run and config_string is not None:
            try:
                regex = r"\d+.\d+.\d+-\d+"
                version_on_node = re.findall(regex, config_string, re.MULTILINE)[0]
            except Exception as e:
                self.console("Obsolete node version - node version was not defined: {}".format(e), state='warn')
                version_on_node = 0
        else:
            version_on_node = "dummy version"
        return version, version_on_node


if __name__ == "__main__":
    b = Compile(dry_run=True)
    version = b.get_micros_version_from_repo()
    print('version: {}'.format(version))
    status = b.precompile_micros()
    print('compilation verdict: {}'.format(status))
