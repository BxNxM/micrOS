import os.path
import sys
import time

try:
    from .micrOSClient import micrOSClient, color
except:
    from micrOSClient import micrOSClient, color


class Executor:

    def __init__(self, host=None, pwd="ADmin123", verbose=False):
        self.com = None
        self.host = host
        self.pwd = pwd
        self.verbose = verbose

    def init_com(self):
        self.com = micrOSClient(host=self.host, port=9008, pwd=self.pwd, dbg=self.verbose)

    def run(self, cmd, force_close=True):
        if self.com is None:
            self.init_com()
        # [2] Test functions for command send function
        print(f"{color.WARN}==> SEND: {cmd}{color.NC}")
        out = self.com.send_cmd_retry(cmd)
        print(f"{cmd}: {out}")
        if force_close: self.com.close()
        return True if len(out) > 0 else False, out


    @staticmethod
    def filter_commands(cmd):
        cmd = cmd.strip()
        if cmd.startswith("wait"):
            wait_cmd = cmd.split()
            wait = int(wait_cmd[1]) if len(wait_cmd) > 1 else 1
            print(f"{cmd}")
            time.sleep(wait)
            return None
        return cmd

    @staticmethod
    def validate_conf(conf):
        is_valid = False
        parsed_config = {'dbg': False, 'device': None, 'pwd': "ADmin123"}
        conf_list = conf.strip().split()
        if len(conf_list) < 2:
            print(f"Not enough parameters:\n#microscript devName.local/IPaddress\n\t{conf}")
            sys.exit(3)
        if conf_list[0] == "#microscript":
            is_valid = True
            parsed_config['dbg'] = "debug" in conf_list
            if parsed_config['dbg']:
                conf_list.remove("debug")
            parsed_config['device'] = conf_list[1]
            if len(conf_list) > 2:
                parsed_config['pwd'] = conf_list[2]
        return is_valid, parsed_config

    @staticmethod
    def create_template(path):
        default_conf = """#microscript __simulator__.local
# Comments:
#       SHEBANG LINE: #microscript <device> <password> <opts>
#           <device>    :   host name or IP address
#           <password>  :   optional parameter, defualt: ADmin123
#           <opts>      :   additional optional params, like: debug
#
# You can list any load module call to be executed...
#
# Additional script commands:
#   wait X      - seconds to wait before execute next command
#   #           - line comment

system top
system clock
wait 1
system clock

"""

        print(f"Create template for {path}")
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
            print("Invalid initial line, must starts with #microscript")
            sys.exit(2)

        print(f"microSCRIPT\nconf:{conf}\ncommands:\n{lines}")
        if self.com is None:
            self.host = conf['device']
            self.verbose = conf['dbg']
            self.pwd = conf['pwd']
        try:
            for cmd in lines:
                cmd = self.filter_commands(cmd)
                if cmd is None:
                    continue
                state, out = self.run(cmd, force_close=False)
                if not state:
                    print("Communication was broken...")
                    break
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            if self.com is not None:
                self.com.close()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Missing file input")
        sys.exit(1)
    MICROSCRIPT_PATH = sys.argv[1]
    executor = Executor()
    executor.run_micro_script(MICROSCRIPT_PATH)
