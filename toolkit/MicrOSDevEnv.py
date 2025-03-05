#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json

MYPATH = os.path.dirname(__file__)
print("Module [MicrOSDevEnv] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYPATH))

try:
    from .DevEnvOTA import OTA
    from .DevEnvUSB import USB
    from .DevEnvCompile import Compile
    from .lib import LocalMachine
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    from DevEnvOTA import OTA
    from DevEnvUSB import USB
    from DevEnvCompile import Compile
    from lib import LocalMachine


class MicrOSDevTool(OTA, USB):

    def __init__(self, dummy_exec=False, gui_console=None, cmdgui=True):
        self.dummy_exec = dummy_exec
        OTA.__init__(self, cmdgui=cmdgui, gui_console=gui_console, dry_run=dummy_exec)
        USB.__init__(self, dry_run=dummy_exec)
        # handle space in path: command line "escape path fix"
        self.micros_sim_resources = os.path.join(MYPATH, 'simulator_lib')
        self.sfuncman_output_path = os.path.join(MYPATH, "../micrOS/client/sfuncman/")

    #####################################################
    #                    DevEnv METHODS                 #
    #####################################################
    def precompile_micros(self):
        micros_dev_env = Compile.is_mpycross_available()
        if not micros_dev_env:
            self.console("SKIP PRECOMPILE - DEV ENV INACTIVE\n\t-> mpy-cross not available", state='warn')
            return True
        self.console("PRECOMPILE - DEV ENV ACTIVE: mpy-cross available", state='ok')
        state = super(MicrOSDevTool, self).precompile_micros()
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
                self.console("[SIM] Copy micrOS resources: {} -> {}".format(f_path, self.micros_sim_workspace))
                LocalMachine.FileHandler().copy(f_path, self.micros_sim_workspace)

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
        import_cmd = "from {} import {}".format(".dashboard_apps", app_name)
        print("[APP] Import: {}".format(import_cmd))
        exec(import_cmd)
        if password is None:
            print(f"[APP] Exec: {app_name}.app(devfid='{dev_name}')")
            return_value = eval(f"{app_name}.app(devfid='{dev_name}')")
        else:
            try:
                print(f"[APP] Exec: {app_name}.app(devfid='{dev_name}', pwd='******')")
                return_value = eval(f"{app_name}.app(devfid='{dev_name}', pwd='{password}')")
            except Exception as e:
                print(f"[APP] Exec: {app_name}.app(devfid='{dev_name}' password error: {e}\nRETRY")
                return_value = eval(f"{app_name}.app(devfid='{dev_name}')")
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

    def LM_functions_static_dump_gen(self):
        """
        Generate static module-function provider json description: sfuncman.json
        [!] name dependency with micrOS internal manual provider
        """

        if not os.path.isdir(self.sfuncman_output_path):
            self.console('DOC GEN DISABLED', state="WARN")
            return

        repo_version = self.get_micros_version_from_repo()
        static_help_json_path = os.path.join(self.sfuncman_output_path, 'sfuncman_{}.json'.format(repo_version))
        static_help_html_path = os.path.join(self.sfuncman_output_path, 'sfuncman.html')

        # [PARSING] Collect Load Module function structure buffer
        modules_to_doc = (i.split('.')[0] for i in LocalMachine.FileHandler.list_dir(self.micrOS_dir_path) if
                          i.startswith('LM_') and (i.endswith('.py')))
        module_function_dict = {}
        for LM in modules_to_doc:
            LMpath = '{}/{}.py'.format(self.micrOS_dir_path, LM)
            try:
                module_name = LM.replace('LM_', '')
                module_function_dict[module_name] = {}
                with open(LMpath, 'r') as f:
                    decorator = None
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        if 'def ' in line and 'def _' not in line:
                            if '(self' in line or '(cls' in line or (decorator is not None and "staticmethod" in decorator):
                                continue
                            # Gen proper func name
                            command = '{}'.format(line.split(')')[0]).replace("def", '').strip()
                            command = command.replace('(', ' ') \
                                .replace(',', '') \
                                .replace('msgobj=None', '') \
                                .replace('force=True', '')
                            func = command.strip().split()[0]
                            param = ' '.join(command.strip().split()[1:])
                            # Save record
                            if module_function_dict[module_name].get(func, None) is None:
                                module_function_dict[module_name][func] = {}
                            module_function_dict[module_name][func]['param(s)'] = param if len(param) > 0 else ""
                        elif line.strip().startswith("@"):
                            decorator = line.strip()
                        else:
                            decorator = None
                # Create / update module data fields
                module_function_dict[module_name]['img'] = f"https://github.com/BxNxM/micrOS/blob/master/media/lms/{module_name}.png?raw=true"
            except Exception as e:
                self.console("STATIC micrOS HELP GEN: LM [{}] PARSER ERROR: {}".format(LM, e))

        # Prepare (update simulator workspace)
        self.simulator(prepare_only=True)
        self.console("[SIM] ADD simulator resources to python path")
        sys.path.append(self.micros_sim_resources)
        import simulator
        sim_proc = simulator.micrOSIM(doc_resolve=True)
        # Generate function doc-strings and pinmap info
        _out = sim_proc.gen_lm_doc_json_html(module_function_dict)
        if _out is None:
            self.console("#########################", state='ERR')
            self.console("#  DOC STRING GEN ERROR #", state='ERR')
            self.console("# -[micrOSIM][DOC ERR]- #", state='ERR')
            self.console("#########################", state='ERR')
            module_function_dict_html = module_function_dict
        else:
            # Unpack output
            module_function_dict, module_function_dict_html = _out

        hardcoded_manual = {"task": {"list": {"doc": "list micrOS tasks by taskID", "param(s)": ""},
                                     "kill": {"doc": "kill / stop micrOS task", "param(s)": "taskID"},
                                     "img": "https://github.com/BxNxM/micrOS/blob/master/media/lms/tasks.png?raw=true"}
                            }

        # [JSON] Dump generated Load Module description: static function manual: sfuncman.json
        module_function_dict.update(hardcoded_manual)
        self.console("Dump micrOS static manual: {}".format(static_help_json_path))
        with open(static_help_json_path, 'w') as f:
            json.dump(module_function_dict, f, indent=4, sort_keys=True)

        # +[HTML] Convert dict to json -> html table
        _url = hardcoded_manual["task"]["img"]
        hardcoded_manual['task']['img'] = f'<img src="{_url}" alt="tasks" height=150>'
        module_function_dict_html.update(hardcoded_manual)
        import json2html
        table_attributes = 'border="1" cellspacing="1" cellpadding="5" width="80%"'

        sorted_modules_w_data = dict(sorted(module_function_dict_html.items(), key=lambda item: item[0].lower()))
        module_shortcuts = ' | '.join(
            f'<a href="#{mod_name.replace(" ", "_")}">{mod_name}</a>'
            for mod_name in sorted_modules_w_data)
        html_tables = module_shortcuts + "<br><hr><br>"
        for key, value in sorted_modules_w_data.items():
            anchor = key.replace(" ", "_")  # Replace spaces with underscores for a valid anchor
            html_tables += f'\n<br><br>\n<h2 id="{anchor}"><a href="#{anchor}">{key}</a></h2>\n'
            html_tables += json2html.json2html.convert(json=value,
                                             table_attributes=table_attributes,
                                             clubbing=True,
                                             escape=False,
                                             encode=False)

        # http://corelangs.com/css/table/tablecolor.html
        # http://corelangs.com/css/table/tablecolor.html

        html_body_start = """<!DOCTYPE html>
<html>
<head>
<title>micrOS Load Modules</title>
<style>
  table,th,td
  {
    border:2px solid black;
    color:black;
  }
  table{border-collapse:collapse;width:80%;}
  td{height:40px;}
  
  tbody tr:nth-child(even){background: rgb(82, 122, 122);}

</style>
</head>

<body style="background-color:LightGray;">
<h1 style="background-color: rgb(82, 122, 122);">
<img src="https://github.com/BxNxM/micrOS/blob/master/media/logo_mini.png?raw=true" target="_blank" alt="{mod}" height=150>
micrOS Load Modules
</h1>
<p>
    <b>Generated function manual with module doc strings.</b><br>
    <a href="https://github.com/BxNxM/micrOS/tree/master/micrOS/client/sfuncman" target="_blank">JSON formatted manuals</a>
</p>

<h2>
Logical pin names aka pin map
</h2>
    <b> Multi-platform pinmap IO handling feature - resolve pin number by name (tag)<br>
    <b>[i] Use 'module_name pinmap()' function to get pins on a runtime system (micrOS shell) and start DIY</b>
<ul>
  <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/IO_esp32.py" target="_blank">esp32</a></li>
  <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/IO_esp32s3.py" target="_blank">esp32s3</a></li>
  <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/IO_m5stamp.py" target="_blank">m5stamp</a></li>
  <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/IO_tinypico.py" target="_blank">tinypico</a></li>
  <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/IO_esp32c3.py" target="_blank">esp32c3</a></li>
  <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/IO_esp32s2.py" target="_blank">esp32s2</a></li>
  <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/IO_rp2.py" target="_blank">rp2 (experimental)</a></li>
</ul>

<h2>
Built-in control modules for various peripheries.:
</h2>

"""
        html_body_end = """</body>
</html>"""

        html_page = html_body_start + html_tables + html_body_end
        # Write html to file
        with open(static_help_html_path, 'w') as f:
            f.write(html_page)


if __name__ == "__main__":
    d = MicrOSDevTool()
    d.LM_functions_static_dump_gen()
