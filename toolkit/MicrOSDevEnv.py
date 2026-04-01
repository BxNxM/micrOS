#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import importlib

MYPATH = os.path.dirname(__file__)
print("Module [MicrOSDevEnv] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYPATH))

SFUNCMAN_HTML_CSS = """
:root {
    --bg: #0b1117;
    --surface: rgba(16, 23, 31, 0.92);
    --surface-soft: rgba(255, 255, 255, 0.03);
    --text: #e7edf4;
    --muted: #97a6b4;
    --line: rgba(231, 237, 244, 0.08);
    --accent: #4e9f75;
    --accent-soft: rgba(78, 159, 117, 0.14);
    --info: #7bc7db;
    --shadow: 0 24px 80px rgba(0, 0, 0, 0.34);
    --radius: 24px;
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    min-height: 100vh;
    padding: 28px;
    color: var(--text);
    font-family: "Avenir Next", "Segoe UI", "Helvetica Neue", sans-serif;
    overflow-x: hidden;
    background:
        radial-gradient(circle at top left, rgba(78, 159, 117, 0.08), transparent 28%),
        radial-gradient(circle at top right, rgba(123, 199, 219, 0.08), transparent 22%),
        linear-gradient(180deg, #0f1720 0%, var(--bg) 100%);
}

a {
    color: inherit;
}

.page {
    max-width: 1220px;
    margin: 0 auto;
    display: grid;
    gap: 20px;
    min-width: 0;
}

.panel {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    backdrop-filter: blur(18px);
}

.hero {
    padding: 28px;
    display: flex;
    justify-content: space-between;
    gap: 20px;
    flex-wrap: wrap;
    align-items: center;
}

.brand {
    display: flex;
    gap: 16px;
    align-items: center;
}

.brand img {
    width: 72px;
    height: 72px;
    border-radius: 20px;
    background: linear-gradient(145deg, #1c2631, #121a23);
    box-shadow: inset 0 0 0 1px rgba(231, 237, 244, 0.06);
    padding: 10px;
}

.eyebrow {
    display: inline-flex;
    padding: 7px 12px;
    border-radius: 999px;
    background: var(--accent-soft);
    color: var(--accent);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

h1 {
    margin: 10px 0 8px;
    font-size: clamp(2rem, 5vw, 3.4rem);
    line-height: 0.96;
    letter-spacing: -0.04em;
}

h2 {
    margin: 0 0 16px;
    font-size: 1.2rem;
    letter-spacing: -0.02em;
}

h3 {
    margin: 0;
    font-size: 1rem;
}

p {
    margin: 0;
    color: var(--muted);
    line-height: 1.65;
}

.hero-links {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.hero-links a,
.shortcut-list a,
.package-links a {
    text-decoration: none;
    padding: 10px 14px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--line);
}

.section {
    padding: 24px;
}

.section-copy {
    display: grid;
    gap: 10px;
}

.pinmap-list {
    margin: 0;
    padding-left: 18px;
    color: var(--muted);
    columns: 2;
}

.pinmap-list li {
    margin: 0 0 8px;
}

.shortcut-list,
.package-links {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.module-grid {
    display: grid;
    gap: 20px;
    min-width: 0;
}

.module-nav {
    padding: 20px 24px;
}

.module-sections {
    display: grid;
    gap: 18px;
}

.module-card {
    padding: 22px;
    min-width: 0;
}

.module-card h2 a {
    text-decoration: none;
}

.doc-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 14px;
    border: 1px solid var(--line);
    border-radius: 16px;
    overflow: hidden;
    display: block;
    max-width: 100%;
    overflow-x: auto;
}

.doc-table th,
.doc-table td {
    border: 1px solid var(--line);
    padding: 12px 14px;
    vertical-align: top;
    text-align: left;
    overflow-wrap: anywhere;
    word-break: break-word;
}

.doc-table th {
    width: 170px;
    color: var(--text);
    background: rgba(255, 255, 255, 0.04);
}

.doc-table td {
    color: var(--muted);
    background: rgba(255, 255, 255, 0.02);
}

.doc-table tr:nth-child(even) td,
.doc-table tr:nth-child(even) th {
    background: rgba(255, 255, 255, 0.035);
}

.doc-table img {
    max-width: 160px;
    height: auto;
    border-radius: 14px;
    display: block;
}

code {
    font-family: "SFMono-Regular", "Menlo", "Monaco", monospace;
}

@media (max-width: 900px) {
    .pinmap-list {
        columns: 1;
    }
}

@media (max-width: 640px) {
    body {
        padding: 16px;
    }

    .hero,
    .section,
    .module-nav,
    .module-card {
        padding: 18px;
    }

    .doc-table th,
    .doc-table td {
        display: block;
        width: 100%;
    }
}
"""

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

    def _build_doc_load_module_structure(self):

        def _is_private_func(_line):
            nonlocal decorator, line
            if 'def ' in line and 'def _' not in line:
                if "async" in line and decorator is not None and "@micro_task" in decorator:
                    # Enable (adjust) async task method with publish_micro_task decorator
                    line = line.replace("async", "").strip()
                    return False
                if '(self' in line or '(cls' in _line or (decorator is not None and "staticmethod" in decorator):
                    # Ignore class methods
                    return True
                return False
            # Ignore non functions, and hidden functions (starts with _)
            return True

        # [PARSING] Collect Load Module function structure buffer
        modules_sim_path = os.path.join(self.micros_sim_workspace, "modules")
        if LocalMachine.FileHandler.path_is_exists(modules_sim_path):
            modules_path = modules_sim_path
        else:
            modules_path = os.path.join(self.micrOS_dir_path, "modules")
        self.console(f"[DOC-GEN] INPUT MODULES PATH: {modules_path}")
        modules_to_doc = [i.split('.')[0] for i in LocalMachine.FileHandler.list_dir(modules_path) if
                          i.startswith('LM_') and (i.endswith('.py'))]
        module_function_dict = {}
        for LM in modules_to_doc:
            LMpath = '{}/{}.py'.format(modules_path, LM)
            try:
                module_name = LM.replace('LM_', '')
                module_function_dict[module_name] = {}
                with open(LMpath, 'r') as f:
                    decorator = None
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        if _is_private_func(line):
                            if line.strip().startswith("@"):
                                decorator = line.strip()
                            else:
                                decorator = None
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

                # Create / update module data fields
                module_function_dict[module_name][
                    'img'] = f"https://github.com/BxNxM/micrOS/blob/master/media/lms/{module_name}.png?raw=true"
            except Exception as e:
                self.console("STATIC micrOS HELP GEN: LM [{}] PARSER ERROR: {}".format(LM, e))
        self.console(f"[DOC-GEN] Detected modules: {module_function_dict.keys()}")
        return module_function_dict

    def LM_functions_static_dump_gen(self):
        """
        Generate static module-function provider json description: sfuncman.json
        [!] name dependency with micrOS internal manual provider
        """

        def _my_json_to_html(mod_func_dict, title="Built-in Control Modules", description=None, section_id=None):
            import json2html
            table_attributes = 'class="doc-table"'

            sorted_modules_w_data = dict(sorted(mod_func_dict.items(), key=lambda item: item[0].lower()))
            module_shortcuts = ''.join(
                f'<a href="#{mod_name.replace(" ", "_")}">{mod_name}</a>'
                for mod_name in sorted_modules_w_data)
            title_id_attr = f' id="{section_id}"' if section_id else ''
            description_html = f'<p>{description}</p>' if description else ''
            html_tables = (
                f'<div class="panel module-nav"{title_id_attr}>'
                f'<h2>{title}</h2>'
                f'{description_html}'
                f'<div class="shortcut-list">{module_shortcuts}</div>'
                '</div>'
            )
            html_tables += '<div class="module-sections">'
            for key, value in sorted_modules_w_data.items():
                anchor = key.replace(" ", "_")  # Replace spaces with underscores for a valid anchor
                html_tables += f'\n<section class="panel module-card">\n<h2 id="{anchor}"><a href="#{anchor}">{key}</a></h2>\n'
                html_tables += json2html.json2html.convert(json=value,
                                                           table_attributes=table_attributes,
                                                           clubbing=True,
                                                           escape=False,
                                                           encode=False)
                html_tables += '\n</section>\n'
            html_tables += '</div>'
            return html_tables

        if not os.path.isdir(self.sfuncman_output_path):
            self.console('DOC GEN DISABLED', state="WARN")
            return

        repo_version = self.get_micros_version_from_repo()
        static_help_json_path = os.path.join(self.sfuncman_output_path, 'sfuncman_{}.json'.format(repo_version))
        static_help_html_path = os.path.join(self.sfuncman_output_path, 'sfuncman.html')

        # Prepare (update simulator workspace)
        self.simulator(prepare_only=True)
        self.console("[SIM] ADD simulator resources to python path")
        sys.path.append(self.micros_sim_resources)
        import simulator
        sim_proc = simulator.micrOSIM(doc_resolve=True)
        # Generate function doc-strings and pinmap info
        module_function_dict = self._build_doc_load_module_structure()
        _out = sim_proc.gen_lm_doc_json_html(module_function_dict)
        if _out is None:
            self.console("#########################", state='ERR')
            self.console("#  DOC STRING GEN ERROR #", state='ERR')
            self.console("# -[micrOSIM][DOC ERR]- #", state='ERR')
            self.console("#########################", state='ERR')
            module_function_dict_html = module_function_dict
            module_function_dict_ext = {}
            module_function_dict_html_ext = {}
        else:
            # Unpack output
            (module_function_dict, module_function_dict_html,
             module_function_dict_ext, module_function_dict_html_ext) = _out

        # Merge built-in and external packages at json dco level (unified document) - external modules has annotation by default
        module_function_dict.update(module_function_dict_ext)
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
        html_tables = _my_json_to_html(
            module_function_dict_html,
            title="Built-in Control Modules",
            description="Compact module index and generated function reference for the current micrOS repository state."
        )
        html_tables_ext = _my_json_to_html(
            module_function_dict_html_ext,
            title="External Modules",
            description="Installable package documentation generated alongside built-in load modules.",
            section_id="external-modules"
        )
        if len(html_tables_ext) > 0:
            html_tables_ext = f"\n{html_tables_ext}\n"

        html_body_start = f"""<!DOCTYPE html>
<html>
<head>
<title>micrOS Load Modules</title>
<style>
{SFUNCMAN_HTML_CSS}
</style>
</head>

<body>
<main class="page">
<section class="panel hero">
    <div class="brand">
        <img src="https://github.com/BxNxM/micrOS/blob/master/media/logo_mini.png?raw=true" alt="micrOS logo">
        <div>
            <div class="eyebrow">Generated Manual</div>
            <h1>micrOS Load Modules</h1>
            <p>Static reference for built-in and external module functions, including pin maps, parameter shapes, and doc strings.</p>
        </div>
    </div>
    <div class="hero-links">
        <a href="https://github.com/BxNxM/micrOS/tree/master/micrOS/client/sfuncman" target="_blank">JSON Manuals</a>
        <a href="#external-modules">External Packages</a>
        <a href="https://github.com/BxNxM/micrOSPackages" target="_blank">Package Repo</a>
    </div>
</section>

<section class="panel section">
    <h2>microIO Pin Mapping</h2>
    <div class="section-copy">
        <p>Resolve logical pin names to integer values across supported boards.</p>
        <p>Use <code>module_name pinmap()</code> on a runtime system to inspect the active pin mapping before wiring hardware.</p>
        <ul class="pinmap-list">
            <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/modules/IO_m5stamp.py" target="_blank">m5stamp</a></li>
            <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/modules/IO_tinypico.py" target="_blank">tinypico</a></li>
            <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/modules/IO_s3matrix.py" target="_blank">s3matrix</a></li>
            <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/modules/IO_esp32.py" target="_blank">esp32</a></li>
            <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/modules/IO_esp32s3.py" target="_blank">esp32s3</a></li>
            <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/modules/IO_esp32c3.py" target="_blank">esp32c3</a></li>
            <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/modules/IO_esp32c6.py" target="_blank">esp32c6</a></li>
            <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/modules/IO_esp32s2.py" target="_blank">esp32s2</a></li>
            <li><a href="https://github.com/BxNxM/micrOS/blob/master/micrOS/source/modules/IO_rp2.py" target="_blank">rp2 (experimental)</a></li>
        </ul>
    </div>
</section>

<div class="module-grid">
"""
        html_body_end = """</body>
</html>"""

        html_page = html_body_start + html_tables + html_tables_ext + "\n</div>\n</main>\n" + html_body_end
        # Write html to file
        with open(static_help_html_path, 'w') as f:
            f.write(html_page)


if __name__ == "__main__":
    d = MicrOSDevTool()
    d.LM_functions_static_dump_gen()
