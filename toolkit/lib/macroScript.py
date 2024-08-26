import os
import sys
import time
from datetime import datetime
import subprocess
import platform


try:
    from .micrOSClient import micrOSClient, color
except:
    from micrOSClient import micrOSClient, color

#####################################
#           HELPER FUNCTIONS        #
#####################################

def _elapsed_time(start, stop):
    # Calculate the difference (delta) between the end and start times
    delta = stop - start

    # Total seconds in the delta
    total_seconds = int(delta.total_seconds())

    # Calculate days, hours, minutes, and seconds
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Formatting the delta time
    formatted_delta = f"{days}d {hours}h {minutes}m {seconds}s"
    return formatted_delta


def _run_internal_macro(macro_name, workdir, verbose=None, safe=None):
    macro_name = f"{macro_name}.macro"
    macro_path = os.path.join(workdir, macro_name)
    print(f"|      - {macro_path}")
    macro_exec = Executor(verbose=verbose, safe=safe)
    macro_exec.run_micro_script(macro_path)


def action_console(action, msg):
    if action == "SKIP":
        action = f"{color.BOLD}--- {action}{color.NC}"
    if action == "SEND":
        action = f"{color.WARN}==> {action}{color.NC}"
    if action == "SHELL":
        action = f"{color.HEADER}*** {action}{color.NC}"
    if action == "WAIT":
        action = f"{color.OKBLUE}=== {action}{color.NC}"
    if action == "MACRO":
        action = f"{color.OKGREEN}=== {action}{color.NC}"
    if action == "ERR":
        action = f"{color.ERR}=== {action}{color.NC}"
    if action == "INIT":
        print(msg)
        return
    message = f"|  {action} {msg}"
    print(message)


def _run_shell_command(command):
    """Run a command in the detected shell."""

    def detect_shell():
        """Detect the current shell type."""
        if platform.system() == "Windows":
            return os.getenv('ComSpec')  # Typically cmd.exe on Windows
        else:
            return os.getenv('SHELL')    # Typically /bin/bash, /bin/zsh, etc. on Unix-like systems

    shell = detect_shell()
    if not shell:
        raise EnvironmentError("Could not detect the shell type.")
    # Execute the command in the detected shell
    result = subprocess.run(command, shell=True, executable=shell, capture_output=True, text=True)
    return shell, result

#####################################
#           MACRO EXECUTOR          #
#####################################

class Executor:

    def __init__(self, host=None, pwd=None, verbose=None, safe=None):
        self.com = None
        self.host = host
        self.pwd = pwd
        self.verbose = verbose
        self.safe_mode = safe
        self.safe_modules = None
        self.workdir = None

    def init_com(self):
        self.com = micrOSClient(host=self.host, port=9008, pwd=self.pwd, dbg=self.verbose)
        if self.safe_mode:
            self.safe_modules = self.com.send_cmd_retry("modules")[0]

    def run(self, cmd, force_close=True):
        if self.com is None:
            self.init_com()
        if self.safe_mode and cmd.split()[0] not in self.safe_modules:
            action_console("SKIP", f"{cmd.split()[0]} execution (not loaded) - safe mode: {self.safe_modules}")
            return True, "Skipped..."
        # [2] Test functions for command send function
        action_console("SEND", cmd)
        out = self.com.send_cmd_retry(cmd)
        action_console(" "*8, f"{cmd}: {out}")
        if force_close: self.com.close()
        return True if len(out) > 0 else False, out

    def filter_commands(self, cmd):
        cmd = cmd.strip()
        # HANDLE wait COMMAND
        if cmd.startswith("WAIT"):
            wait_cmd = cmd.split()
            wait = int(wait_cmd[1]) if len(wait_cmd) > 1 else 1
            action_console("WAIT", cmd)
            time.sleep(wait)
            return None
        # HANDLE wait COMMAND
        if cmd.startswith("MACRO"):
            action_console("MACRO", cmd)
            _run_internal_macro(cmd.split()[1].strip(), self.workdir, verbose=self.verbose, safe=self.safe_mode)
            return None
        if cmd.startswith("SHELL"):
            action_console("SHELL", cmd)
            cmd = ' '.join(cmd.split()[1:])
            try:
                shell, result = _run_shell_command(cmd)
                stdout = result.stdout.strip()
                stderr = result.stderr.strip()
                action_console(" " * 8, f"[{result.returncode}] {shell} {cmd}\n{stdout}\n{stderr}")
            except Exception as e:
                action_console("ERR", f"NoShell: {e}")
            return None
        return cmd

    @staticmethod
    def validate_conf(conf):
        is_valid = False
        parsed_config = {'dbg': False, 'device': None, 'pwd': "ADmin123", 'safe': False}
        conf_list = conf.strip().split()
        if len(conf_list) < 2:
            print(f"Not enough parameters:\n#macroscript devName.local/IPaddress\n\t{conf}")
            sys.exit(3)
        if conf_list[0] == "#macroscript":
            is_valid = True
            parsed_config['dbg'] = "debug" in conf_list
            if parsed_config['dbg']:
                conf_list.remove("debug")
            parsed_config['safe'] = "safe" in conf_list
            if parsed_config['safe']:
                conf_list.remove("safe")
            parsed_config['device'] = conf_list[1]
            if len(conf_list) > 2:
                parsed_config['pwd'] = conf_list[2]
        return is_valid, parsed_config

    @staticmethod
    def create_template(path):
        default_conf = """#macroscript 127.0.0.1 safe
#
# HINTS:
#   SHEBANG LINE: #macroscript <device> <password> <opts>
#       <device>    :   host name or IP address
#       <password>  :   optional parameter, defualt: ADmin123
#       <opts>      :   additional optional params:
#           debug   :   show verbose output
#           safe    :   only run loaded modules
#
# You can list any load module function call to be remotely executed
#
# Additional script commands:
#   WAIT <s>        - seconds to wait before execute next command
#   MACRO <name>    - run a macro by name (from same dir as parent macro)
#   SHELL <command> - run shell oneliners
#   #               - line comment

system top
system clock
WAIT 1
system clock

"""

        print(f"{color.OKGREEN}Create template for{color.NC} {path}")
        with open(path, 'w') as f:
            f.write(default_conf)

    def run_micro_script(self, path):
        if not (os.path.exists(path) and path.endswith(".macro")):
            print(f"No file was found: {path} or extension is not .macro")
            self.create_template(path)
            return
        with open(path, 'r') as f:
            lines = [ l for l in f.read().strip().splitlines() if len(l.strip()) > 0 ]
            conf = lines.pop(0)
        lines  = [ l for l in lines if not l.strip().startswith("#") ]
        conf_is_valid, conf = self.validate_conf(conf)
        if not conf_is_valid:
            print("Invalid initial line, must starts with #macroscript")
            sys.exit(2)

        action_console("INIT", f"{color.BOLD}{color.OK}macroSCRIPT{color.NC}: {os.path.basename(path)}")
        #print(f"conf:{conf}\ncommands:{lines}")
        if self.com is None:
            # Inject params from macro if was not set by constructor
            self.host = conf['device'] if self.host is None else self.host
            self.verbose = conf['dbg'] if self.verbose is None else self.verbose
            self.pwd = conf['pwd'] if self.pwd is None else self.pwd
            self.safe_mode = conf['safe'] if self.safe_mode is None else self.safe_mode
            self.workdir = os.path.dirname(path)
        start_time = datetime.now()
        cmd_cnt = 0
        try:
            for cmd in lines:
                cmd = self.filter_commands(cmd)
                if cmd is None:
                    continue
                cmd_cnt += 1
                state, out = self.run(cmd, force_close=False)
                if not state:
                    print("Communication was broken...")
                    break
        except Exception as e:
            print(f"Connection error {os.path.basename(path)}: {e}")
        finally:
            if self.com is not None:
                self.com.close()
        end_time = datetime.now()
        elapsed = _elapsed_time(start_time, end_time)
        print(f"[{color.BOLD}{color.OK}{os.path.basename(path)}{color.NC}] Elapsed time: {elapsed} / {cmd_cnt} command(s).")



if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Missing file input")
        sys.exit(1)
    MICROSCRIPT_PATH = sys.argv[1]
    executor = Executor()
    executor.run_micro_script(MICROSCRIPT_PATH)
