import os
import sys
import time
from datetime import datetime
import subprocess
import platform
import threading
try:
    from .micrOSClient import micrOSClient, color
except:
    from micrOSClient import micrOSClient, color
try:
    import curses
except Exception as e:
    print(f"Missing dependency for curses: {e}")
    curses = None

DRY_RUN = False

#####################################
#         FILE SELECTION TUI        #
#####################################

def select_menu(directory):
    if not os.path.isdir(directory):
        print("Not a directory.")
        return None
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith(".macro")]
    if not files:
        print("No macro found in the directory.")
        return None

    def macro_preview(path):
        with open(path, 'r') as file:
            # Read the first line
            first_line = file.readline().strip()
        preview = ' '.join(first_line.split()[1:])
        macro_name_len = len(os.path.basename(path))
        column_idx = 30
        spacer = " " * (column_idx - macro_name_len)
        return f"{spacer}{preview}"

    def display_menu(stdscr):
        if curses is None:
            return None
        curses.curs_set(0)  # Hide the cursor
        current_row = 0
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "Please select a macro:")
            # Display files with navigation
            for idx, file in enumerate(files):
                if idx == current_row:
                    stdscr.addstr(idx + 1, 2, f"> {file} {macro_preview(os.path.join(directory, file))}", curses.A_REVERSE)  # Highlight the current selection
                else:
                    stdscr.addstr(idx + 1, 2, f"  {file}")
            key = stdscr.getch()
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(files) - 1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                stdscr.clear()
                #stdscr.addstr(0, 0, f"Macro selected: {files[current_row]}")
                #stdscr.refresh()
                #stdscr.getch()  # Wait for another key press before exiting
                return os.path.join(directory, files[current_row])
    return curses.wrapper(display_menu)


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
    if action == "RECURSION":
        action = f"{color.WARN}{color.BOLD}    &&& {action}{color.NC}"
    if action == "INIT":
        print(msg)
        return
    dr = "DRYRUN" if DRY_RUN else ""
    message = f"{dr}|  {action} {msg}"
    print(message)


#####################################
#           MACRO EXECUTOR          #
#####################################

class Executor:
    RECURSION_COUNTER = {}

    def __init__(self, host=None, pwd=None, verbose=None, safe=None, parallel=None, max_recursion=5):
        self.com = None
        self.host = host
        self.pwd = pwd
        self.verbose = verbose
        self.safe_mode = safe
        self.safe_modules = None
        self.workdir = None
        self.macro_name = None
        self.max_recursion = max_recursion
        self.parallel = parallel

    def init_com(self):
        try:
            self.com = micrOSClient(host=self.host, port=9008, pwd=self.pwd, dbg=self.verbose)
            if self.safe_mode:
                self.safe_modules = self.com.send_cmd_retry("modules")[0]
        except Exception as e:
            print(f"Connection error, cannot get dhcp(?): {e}")
            if DRY_RUN:
                self.com.close = lambda: print("DRY_RUN close")
                self.safe_modules = []
                return
            raise e

    def run(self, cmd, force_close=True):
        if self.com is None:
            self.init_com()
        if self.safe_mode and cmd.split()[0] not in self.safe_modules:
            action_console("SKIP", f"{cmd.split()[0]} execution (not loaded) - safe mode: {self.safe_modules}")
            return True, "Skipped..."
        # [2] Test functions for command send function
        action_console("SEND", cmd)
        if DRY_RUN:
            out = f"dryrun"
        else:
            out = self.com.send_cmd_retry(cmd)
        action_console(" "*8, f"{cmd}: {out}")
        if force_close: self.com.close()
        return True if len(out) > 0 else False, out

    @staticmethod
    def _run_embedded_macro(macro_name, workdir, verbose=None, safe=None, background=None):
        def run():
            nonlocal  macro_name, workdir, verbose, safe, background
            macro_name = f"{macro_name}.macro"
            macro_path = os.path.join(workdir, macro_name)
            print(f"|      - {macro_path}{' - background' if background else ''}")
            macro_exec = Executor(verbose=verbose, safe=safe)
            macro_exec.run_micro_script(macro_path)

        if background:
            thread = threading.Thread(target=run)
            thread.start()
        else:
            run()

    def run_embedded_macro(self, macro_name):
        run_macro = True
        if self.macro_name == macro_name:
            if Executor.RECURSION_COUNTER.get(self.macro_name, None) is None:
                Executor.RECURSION_COUNTER[self.macro_name] = 1
            counter = Executor.RECURSION_COUNTER[self.macro_name]
            if counter >= self.max_recursion:
                action_console("RECURSION", f"{self.macro_name} macro limit exceeded: {self.max_recursion}")
                Executor.RECURSION_COUNTER[self.macro_name] = 1
                run_macro = False
            else:
                action_console("RECURSION", f"{self.macro_name} macro: {counter}/{self.max_recursion}")
                Executor.RECURSION_COUNTER[self.macro_name] += 1
        if run_macro:
            self._run_embedded_macro(macro_name, self.workdir, verbose=self.verbose, safe=self.safe_mode, background=self.parallel)

    @staticmethod
    def _run_shell_command(command):
        """Run a command in the detected shell."""

        def detect_shell():
            """Detect the current shell type."""
            if platform.system() == "Windows":
                return os.getenv('ComSpec')  # Typically cmd.exe on Windows
            else:
                return os.getenv('SHELL')  # Typically /bin/bash, /bin/zsh, etc. on Unix-like systems

        shell = detect_shell()
        if not shell:
            raise EnvironmentError("Could not detect the shell type.")
        # Execute the command in the detected shell
        result = subprocess.run(command, shell=True, executable=shell, capture_output=True, text=True)
        return shell, result

    def filter_commands(self, cmd):
        cmd = cmd.strip()
        # HANDLE wait COMMAND
        if cmd.startswith("WAIT"):
            wait_cmd = cmd.split()
            wait = int(wait_cmd[1]) if len(wait_cmd) > 1 else 1
            action_console("WAIT", cmd)
            if DRY_RUN:
                return None
            time.sleep(wait)
            return None
        # HANDLE wait COMMAND
        if cmd.startswith("MACRO"):
            action_console("MACRO", cmd)
            macro_name = cmd.split()[1].strip()
            self.run_embedded_macro(macro_name)
            return None
        if cmd.startswith("SHELL"):
            action_console("SHELL", cmd)
            cmd = ' '.join(cmd.split()[1:])
            try:
                shell, result = self._run_shell_command(cmd)
                stdout = result.stdout.strip()
                stderr = "\n" + result.stderr.strip()
                action_console(" " * 8, f"[{result.returncode}] {shell} {cmd}\n{stdout}{stderr}")
            except Exception as e:
                action_console("ERR", f"NoShell: {e}")
            return None
        return cmd

    @staticmethod
    def validate_conf(conf):
        is_valid = False
        parsed_config = {'dbg': False, 'device': None, 'pwd': "ADmin123", 'safe': False, 'parallel': False}
        conf_list = conf.strip().split()
        if len(conf_list) < 2:
            print(f"Not enough parameters:\n#macroscript devName.local/IPaddress\n\t{conf}")
            sys.exit(3)
        if conf_list[0] == "#macroscript":
            is_valid = True
            # FLAG: safe
            parsed_config['safe'] = "safe" in conf_list
            if parsed_config['safe']:
                conf_list.remove("safe")
            # FLAG: debug
            parsed_config['dbg'] = "debug" in conf_list
            if parsed_config['dbg']:
                conf_list.remove("debug")
            # FLAG: parallel
            parsed_config['parallel'] = "parallel" in conf_list
            if parsed_config['parallel']:
                conf_list.remove("parallel")
            # PARAM: device
            parsed_config['device'] = conf_list[1]
            # PARAM: pwd
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
#           parallel:   enable parallel macro execution
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
        try:
            self._run_micro_script(path)
        except KeyboardInterrupt:
            print("Exiting...")

    def _run_micro_script(self, path):
        if os.path.isdir(path):
            path = select_menu(path)
            if path is None:
                action_console("ERR", "Cannot find macro for selection menu")
                sys.exit(5)
        if not (os.path.isfile(path) and path.endswith(".macro")):
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

        if self.com is None:
            # Inject params from macro if was not set by constructor
            self.safe_mode = conf['safe'] if self.safe_mode is None else self.safe_mode
            self.verbose = conf['dbg'] if self.verbose is None else self.verbose
            self.parallel = conf['parallel'] if self.parallel is None else self.parallel
            self.host = conf['device'] if self.host is None else self.host
            self.pwd = conf['pwd'] if self.pwd is None else self.pwd
            self.workdir = os.path.dirname(path)
            self.macro_name = os.path.basename(path).split(".")[0].strip()
        action_console("INIT", f"{color.BOLD}{color.OK}\nmacroSCRIPT{color.NC}: {self.macro_name} {color.BOLD}{self.host}{color.NC}")
        if DRY_RUN:
            print(f"conf:{conf}\ncommands:{lines}")
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
            print(f"Connection error {self.macro_name}: {e}")
        finally:
            if self.com is not None:
                self.com.close()
        end_time = datetime.now()
        elapsed = _elapsed_time(start_time, end_time)
        print(f"[{color.BOLD}{color.OK}{self.macro_name}{color.NC}] Elapsed time: {elapsed} / {cmd_cnt} command(s).")



if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Missing file input")
        sys.exit(1)
    MICROSCRIPT_PATH = sys.argv[1]
    executor = Executor()
    executor.run_micro_script(MICROSCRIPT_PATH)
