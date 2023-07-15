import sys
import os
import multiprocessing
import time
import copy

MYPATH = os.path.dirname(__file__)
SIM_PATH = os.path.join(MYPATH, '../workspace/simulator')
sys.path.insert(0, SIM_PATH)
sys.path.insert(0, os.path.join(MYPATH, '../lib'))
from sim_console import console
import micrOSloader
import LocalMachine


class micrOSIM():
    SIM_PROCESS_LIST = []

    def __init__(self, doc_resolve=False):
        if doc_resolve:
            console("[micrOSIM] Create micrOS LM doc (env proc)")
            # json_structure, html_structure
            self.doc_output = (None, None)
        else:
            console("[micrOSIM] INFO: Number of cpu : {}".format(multiprocessing.cpu_count()))
            console("[micrOSIM] Create micrOS simulator process...")
            self.process = multiprocessing.Process(target=self.micrOS_sim_worker)
            self.pid = None
            micrOSIM.SIM_PROCESS_LIST.append(self.process)

    def micrOS_sim_worker(self):
        sim_path = LocalMachine.SimplePopPushd()
        sim_path.pushd(SIM_PATH)
        console("[micrOSIM] Start micrOS loader in: {}".format(SIM_PATH))
        prev_t = time.time()

        def trace_func(frame, event, arg):
            nonlocal prev_t
            elapsed_time = "{:.2e}".format(time.time() - prev_t)
            prev_t = time.time()
            file = frame.f_code.co_filename
            line = frame.f_lineno
            code = frame.f_code.co_name
            if 'simulator/' in file and code != 'idle_task':
                print(f"{' '*50}[trace][{elapsed_time}s][{event}] {line}: {'/'.join(file.split('/')[-1:])}.{code} {arg if arg else ''}")

        # Trace handling - DEBUG
        sys.settrace(trace_func)
        micrOSloader.main()

        console("[micrOSIM] Stop micrOS ({})".format(SIM_PATH))
        sim_path.popd()

    def wait_process(self):
        try:
            self.process.join()
        except Exception as e:
            console(e)

    def start(self):
        console("[micrOSIM] Start micrOS simulator process")
        self.process.start()
        self.pid = self.process.pid
        console("[micrOSIM] micrOS process was started: {}".format(self.pid))

    def terminate(self):
        if self.process.is_alive():
            self.process.terminate()
            while self.process.is_alive():
                console("[micrOSIM] Wait process to terminate: {}".format(self.pid))
                time.sleep(1)
        self.process.close()
        console("[micrOSIM] Proc was finished: {}".format(self.pid))

    @staticmethod
    def stop_all():
        proc_list = micrOSIM.SIM_PROCESS_LIST
        proc_len = len(proc_list)
        for i, proc in enumerate(proc_list):
            try:
                if proc.is_alive():
                    proc.terminate()
                    while proc.is_alive():
                        console("[micrOSIM] Wait process to terminate: {}/{}".format(i+1, proc_len))
                        time.sleep(1)
                proc.close()
            except Exception as e:
                console("[micrOSIM] Proc already stopped: {}/{}: {}".format(i+1, proc_len, e))
            console("[micrOSIM] Proc was finished: {}/{}".format(i+1, proc_len))
        micrOSIM.SIM_PROCESS_LIST = []

    def _lm_doc_strings(self, structure):
        """
        Collect function doc strings and module logical pins (pin map)
        Create 2 dict structures adding docstring
        - html hack structure
        - json raw structure
        """
        structure_to_html = copy.deepcopy(structure)

        # Step into workspace path
        popd = LocalMachine.SimplePopPushd()
        popd.pushd(SIM_PATH)

        # Based on created module-function structure collect doc strings
        for mod, func_dict in structure.items():
            # Embed img url to table - module level
            img_url = structure[mod]['img']
            structure_to_html[mod]['img'] = f'<img src="{img_url}" alt="{mod}" height=150>'
            # Parse function doc strings
            for func in func_dict:
                # -- Skip functions --
                if not isinstance(structure[mod][func], dict):
                    continue
                # -- Skip functions --

                console(f"[micrOSIM][Extract doc-str] LM_{mod}.{func}.__doc__")
                try:
                    # Get function doc string
                    exec(f"import LM_{mod}")
                    doc_str = eval(f"LM_{mod}.{func}.__doc__")
                    # Get function pin map
                    if func == 'pinmap':
                        # Get module pin map - module level
                        console(f"[micrOSIM][Extract pin map tokens] LM_{mod}.pinmap()")
                        try:
                            mod_pinmap = eval(f"LM_{mod}.pinmap()")
                            if mod_pinmap is not None:
                                mod_pinmap = ', '.join(dict(mod_pinmap).keys())
                                mod_pinmap = f"\npin map: {mod_pinmap}"
                        except:
                            mod_pinmap = ''
                        # Add pinmap to doc string of pinmap() function
                        doc_str += mod_pinmap
                except Exception as e:
                    doc_str = str(e)
                # Update structure with doc-str
                structure[mod][func]['doc'] = doc_str
                structure_to_html[mod][func]['doc'] = 'No doc string available' if doc_str is None else doc_str.strip()\
                    .replace('\n', '<br>\n').replace(' ', '&nbsp;')
                # Remove empty param(s) cells
                param_cell = structure_to_html[mod][func].get('param(s)', None)
                if param_cell is not None and len(param_cell.strip()) == 0:
                    structure_to_html[mod][func].pop('param(s)')

        # restore path
        popd.popd()
        self.doc_output = (structure, structure_to_html)

    def gen_lm_doc_json_html(self, structure):
        try:
            proc = multiprocessing.Process(target=self._lm_doc_strings(structure))
            while proc.is_alive():
                time.sleep(0.1)
            return self.doc_output
        except Exception as e:
            console("[micrOSIM][DOC ERR] Doc generation error: gen_lm_doc_json_html: {}".format(e))
        return None


if __name__ == '__main__':
    sim = micrOSIM()
    console("Test mode - Stop after 3 sec")
    sim.start()
    console("Test mode - Stop after 3 sec")
    time.sleep(3)
    sim.terminate()
    micrOSIM.stop_all()

