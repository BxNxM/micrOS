#####################################
#            APP CONFIG             #
#####################################
import os, sys
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(MYPATH))
import socketClient

class AppBase:

    def __init__(self, device:str, password:str):
        self.device = device
        self.password = password

    def base_cmd(self) -> list:
        if self.password is None:
            return ['--dev', self.device]
        return ['--dev', self.device, '--password', self.password]

    def get_device(self):
        return self.device

    def execute(self, cmd_list, tout=5):
        cmd_args = self.base_cmd() + cmd_list
        print(f"Execute: {cmd_args}")
        return socketClient.run(cmd_args, timeout=tout)

    def run(self, cmd_list):
        """Legacy"""
        out = self.execute(cmd_list)
        return out[0], out[1]

    def connection_metrics(self):
        return socketClient.connection_metrics(f"{self.device}.local")
