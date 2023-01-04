import os
import sys
import re
import time

MYPATH = os.path.dirname(__file__)
print("Module [DevEnvBase] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYPATH))

try:
    from .lib import LocalMachine
    from .lib.TerminalColors import Colors
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    from lib import LocalMachine
    from lib.TerminalColors import Colors

try:
    import mpy_cross
    print("{}MICROPYTHON mpy_cross version{}:".format(Colors.WARN, Colors.NC))
    mpy_cross.run('--version')
    time.sleep(0.1)
    print("{}|_ To update mpy_cross{}: source magic.bash env; pip uninstall mpy_cross; pip install mpy_cross".format(
        Colors.WARN, Colors.NC))
except Exception as e:
    print("{}[!!!] mpy-cross error{}: {}".format(Colors.ERR, Colors.NC, e))
    mpy_cross = None


class Compile:

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.micrOS_dir_path = os.path.join(MYPATH, "../micrOS/source")
        self.precompiled_micrOS_dir_path = os.path.join(MYPATH, "workspace/precompiled")
        self.sfuncman_output_path = os.path.join(MYPATH, "../micrOS/client/sfuncman/")
        self.precompile_LM_whitelist = self._read_LMs_whitelist()
        self.python_interpreter = sys.executable.replace(" ", "\ ")
        self.micros_sim_workspace = os.path.join(MYPATH, 'workspace/simulator')
        self.execution_verdict = []
        # mpy-cross binary path for cross compilation
        if mpy_cross is None:
            self.mpy_cross_compiler_path = None
        else:
            self.mpy_cross_compiler_path = mpy_cross.mpy_cross

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
                       if pysource.endswith('.py') or pysource.endswith('.mpy')]:
            to_remove_path = os.path.join(self.precompiled_micrOS_dir_path, source)
            self.console("\t|-remove: {}".format(to_remove_path), state='imp')
            if not self.dry_run:
                LocalMachine.FileHandler.remove(to_remove_path)

    def get_micros_version_from_repo(self):
        # Get repo version
        with open(os.path.join(self.micrOS_dir_path, 'InterpreterShell.py'), 'r') as f:
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
                mpy_cross=self.mpy_cross_compiler_path.replace(" ", "\ "),
                to_compile=to_compile.replace(" ", "\ "),
                target_path=self.precompiled_micrOS_dir_path.replace(" ", "\ "),
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
        # Evaluation summary
        if error_cnt != 0:
            self.console("Some modules [{}] not compiled properly - please check the logs.".format(error_cnt),
                         state='err')
            sys.exit(4)
        else:
            return True

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
    b = Base(dry_run=True)
    version = b.get_micros_version_from_repo()
    print('version: {}'.format(version))
    status = b.precompile_micros()
    print('compilation verdict: {}'.format(status))
