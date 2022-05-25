import sys
import os
import multiprocessing
import time

MYPATH = os.path.dirname(__file__)
SIM_PATH = os.path.join(MYPATH, '../workspace/simulator')
sys.path.insert(0, SIM_PATH)
sys.path.insert(0, os.path.join(MYPATH, '../lib'))
from sim_console import console
import micrOSloader
import LocalMachine


class micrOSIM():
    SIM_PROCESS_LIST = []

    def __init__(self):
        console("INFO: Number of cpu : {}".format(multiprocessing.cpu_count()))
        console("Create micrOS simulator process...")
        self.process = multiprocessing.Process(target=self.micrOS_sim_worker)
        self.pid = None
        micrOSIM.SIM_PROCESS_LIST.append(self.process)

    def micrOS_sim_worker(self):
        sim_path = LocalMachine.SimplePopPushd()
        sim_path.pushd(SIM_PATH)
        console("Start micrOS loader in: {}".format(SIM_PATH))

        micrOSloader.main()

        console("Stop micrOS ({})".format(SIM_PATH))
        sim_path.popd()

    def wait_process(self):
        try:
            self.process.join()
        except Exception as e:
            console(e)

    def start(self):
        console("Start micrOS simulator process")
        self.process.start()
        self.pid = self.process.pid
        console("micrOS process was started: {}".format(self.pid))

    def terminate(self):
        if self.process.is_alive():
            self.process.terminate()
            while self.process.is_alive():
                console("Wait process to terminate: {}".format(self.pid))
                time.sleep(1)
        self.process.close()
        console("Proc was finished: {}".format(self.pid))

    @staticmethod
    def stop_all():
        proc_list = micrOSIM.SIM_PROCESS_LIST
        proc_len = len(proc_list)
        for i, proc in enumerate(proc_list):
            try:
                if proc.is_alive():
                    proc.terminate()
                    while proc.is_alive():
                        console("Wait process to terminate: {}/{}".format(i+1, proc_len))
                        time.sleep(1)
                proc.close()
            except Exception as e:
                console("Proc already stopped: {}/{}: {}".format(i+1, proc_len, e))
            console("Proc was finished: {}/{}".format(i+1, proc_len))
        micrOSIM.SIM_PROCESS_LIST = []


if __name__ == '__main__':
    sim = micrOSIM()
    console("Test mode - Stop after 3 sec")
    sim.start()
    console("Test mode - Stop after 3 sec")
    time.sleep(3)
    sim.terminate()
    micrOSIM.stop_all()

