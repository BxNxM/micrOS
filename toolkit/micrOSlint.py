import os
import json
import sys
from pylint.lint import Run

try:
    from .lib import LocalMachine
    from .lib.TerminalColors import Colors
    from .DevEnvCompile import Compile
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    from lib import LocalMachine
    from lib.TerminalColors import Colors
    from DevEnvCompile import Compile

MYPATH = os.path.dirname(__file__)
MICROS_SOURCE_DIR = os.path.join(MYPATH, '../micrOS/source')
RELEASE_INFO_PATH = os.path.join(MYPATH, '../micrOS/release_info/micrOS_ReleaseInfo')

# MICROS LINTER CONFIG
ALLOWED_LM_DEP_WARNS = 6        # ALLOWED NUMBER OF LM CORE DEPENDENCY (less is better)

def parse_micros_file_categories(verbose=True):
    """
    Parse files into categories: core, load_module, pin_maps, other
    """
    file_ignore_list = ['.DS_Store']
    # micrOS file categories
    categories = {'core': [], 'load_module': [], 'pin_maps': [], 'other': []}
    files = [f for f in LocalMachine.FileHandler.list_dir(MICROS_SOURCE_DIR) if f not in file_ignore_list]
    for f in files:
        if f.startswith('LM_') and f.endswith('.py'):
            categories['load_module'].append(f)
        elif f.startswith('IO_') and f.endswith('.py'):
            categories['pin_maps'].append(f)
        elif f.endswith('.py'):
            categories['core'].append(f)
        else:
            categories['other'].append(f)
    if verbose:
        print("micrOS categorized resources")
        print(json.dumps(categories, sort_keys=True, indent=4))
    return categories


def _parse_py_file_content(file_name, verbose=True):
    source_line_cnt = 0
    source_dependencies = []
    file_path = os.path.join(MICROS_SOURCE_DIR, file_name)
    with open(file_path, 'r') as f:
        file_content = f.read()
    if verbose:
        print(f"Check {file_path}")
    for line in file_content.strip().split('\n'):
        raw_line = line.strip()
        if len(raw_line) > 0 and not raw_line.startswith('#'):     # Ignore: empty lines and single line comments
            source_line_cnt += 1
            # Collect imports from module
            if raw_line.startswith('import') or raw_line.startswith('from'):
                source_dependencies.append(raw_line.split()[1])
        if verbose:
            print(f"[{source_line_cnt}]({len(raw_line)})\t\t{line}")
    if verbose:
        print(f"LINES: {source_line_cnt} IMPORTS: {source_dependencies}")
    return source_line_cnt, source_dependencies


def parse_core_modules(core_resources, verbose=True):
    core_resource_struct = {}
    for file_name in core_resources:
        line_cnt, dependencies = _parse_py_file_content(file_name, verbose=verbose)
        core_resource_struct[file_name] = {'lines': line_cnt, 'dependencies': dependencies}
    if verbose:
        print(f"{'_'*100}\nRUN parse_core_modules")
        print(json.dumps(core_resource_struct, sort_keys=True, indent=4))
    return core_resource_struct


def parse_load_modules(lm_resources, verbose=True):
    lm_resource_struct = {}
    for file_name in lm_resources:
        line_cnt, dependencies = _parse_py_file_content(file_name, verbose=verbose)
        lm_resource_struct[file_name] = {'lines': line_cnt, 'dependencies': dependencies}
    if verbose:
        print(f"{'_'*100}\nRUN parse_load_modules")
        print(json.dumps(lm_resource_struct, sort_keys=True, indent=4))
    return lm_resource_struct


def _update_dep_category(struct, core_filter_list, lm_filter_list, master_key='core'):
    def init_struct():
        nonlocal  categories
        # core->?module?->dependencies
        #                               ->core
        #                               ->builtin
        #                               ->lm
        if categories[master_key].get(core, None) is None:
            categories[master_key][core] = {}
            categories[master_key][core]['dependencies'] = {}
        if categories[master_key][core]['dependencies'].get('core', None) is None:
            categories[master_key][core]['dependencies']['core'] = []
            categories[master_key][core]['dependencies']['builtin'] = []
            categories[master_key][core]['dependencies']['lm'] = []
            categories[master_key][core]['linter'] = {}

    categories = {master_key: {}}
    lines_sum = 0
    for core in struct:
        core_module_dep = struct[core]['dependencies']
        lines = struct[core]['lines']
        lines_sum += lines
        init_struct()
        for mod_dep in core_module_dep:
            # Filter core resources
            if mod_dep in core_filter_list:
                categories[master_key][core]['dependencies']['core'].append(mod_dep)
            elif mod_dep in lm_filter_list:
                # Filter lm resources
                categories[master_key][core]['dependencies']['lm'].append(mod_dep)
            else:
                categories[master_key][core]['dependencies']['builtin'].append(mod_dep)
        try:
            categories[master_key][core]['linter']['lines'] = lines
        except Exception as e:
            print(f"[WARNING] {e}")
            
    categories[master_key]['linter'] = {}
    categories[master_key]['linter']['sum_lines'] = lines_sum
    return categories


def combine_data_structures(core_struct, lm_struct, all_struct, verbose=True):
    # Group system modules and micrOS modules - core
    core_resource_names = [c.split('.')[0] for c in core_struct]
    lm_resource_names = [c.split('.')[0] for c in lm_struct]

    categories_core = _update_dep_category(core_struct, core_resource_names, lm_resource_names, master_key='core')
    categories_lm = _update_dep_category(lm_struct, core_resource_names, lm_resource_names, master_key='load_module')
    categories_other = {'pin_maps': all_struct['pin_maps'], 'other': all_struct['other']}
    categories = {**categories_core, **categories_lm, **categories_other}
    if verbose:
        print(f"{'_'*100}\nRUN combine_data_structures")
        print(json.dumps(categories, sort_keys=True, indent=4))
    return categories


def core_dep_checker(categories, verbose=True):
    # Checker verdict: (dep_name, is_ok, verdict)
    state = True
    verdict = []
    core_resources = categories['core']
    for core_res in core_resources:
        try:
            categories['core'][core_res]['linter']['mlint'] = (True, 'OK')
            lm_dep = core_resources[core_res]['dependencies']['lm']
            if len(lm_dep) > 0:
                verdict.append((core_res, False, f'Core resource has LM dep - ALERT - {lm_dep}'))
                categories['core'][core_res]['linter']['mlint'] = (False, f'Core resource has LM dep - ALERT - {lm_dep}')
                state = False
        except Exception as e:
            if core_res != 'linter':
                state = False
                verdict.append((core_res, True, f'res-error: {e}'))
    if verbose or not state:
        print(f"{'_'*100}\nRUN core_dep_checker ({state})")
        print(json.dumps(verdict, sort_keys=True, indent=4))

    core_dep_warnings = sum([1 for v in verdict if not v[1]])
    return state, core_dep_warnings, categories


def load_module_checker(categories, verbose=True):

    def _is_allowed(_relation):
        _allowed_whitelist = ['Common', 'microIO', 'Types', 'urequests']
        _allowed = []
        for _allow in _relation:
            if _allow in _allowed_whitelist:
                _allowed.append(_allow)
        return _relation, _allowed

    lm_god_mode = ['LM_system.py', 'LM_pacman.py', 'LM_intercon.py']
    state_lm_dep = True
    verdict = []
    lm_resources = categories['load_module']
    for lm_res in lm_resources:
        try:
            categories['load_module'][lm_res]['linter']['mlint'] = (True, 'OK')
            core_relation = lm_resources[lm_res]['dependencies']['core']
            core_relation, allowed = _is_allowed(core_relation)
            if len(core_relation) > len(allowed):
                if lm_res in lm_god_mode:
                    verdict.append((lm_res, True, f'WARNING: lm dep: {core_relation}'))
                    categories['load_module'][lm_res]['linter']['mlint'] = (True, 'OK')
                else:
                    verdict.append((lm_res, False, f'ALERT: lm dep: {core_relation}'))
                    categories['load_module'][lm_res]['linter']['mlint'] = (False, f'LM has direct-core usage (not over Common) - ALERT - {core_relation}')
                    state_lm_dep = False
        except Exception as e:
            if lm_res != 'linter':
                state_lm_dep = False
                verdict.append((lm_res, True, f'res-error: {e}'))

    lm_dep_warnings = sum([1 for v in verdict if not v[1]])
    if lm_dep_warnings <= ALLOWED_LM_DEP_WARNS:  # Temporary fix, drops error if quality pattern goes down...
        # TODO: After fixes it can be set as False in this case, if it make sense
        state_lm_dep = True
    if verbose or not state_lm_dep:
        print(f"{'_'*100}\nRUN load_module_checker ({state_lm_dep})")
        print(json.dumps(verdict, sort_keys=True, indent=4))
    return state_lm_dep, lm_dep_warnings, categories


def _run_pylint(file_name):
    file_path = os.path.join(MICROS_SOURCE_DIR, file_name)
    # Customize pylint options
    pylint_opts = [
        '--disable=import-error',                   # Ignore import error due to micropython deps
        '--disable=missing-class-docstring',        # Disable DOCSTRING: class
        '--disable=missing-function-docstring',     # Disable DOCSTRING: function
        '--disable=line-too-long',                  # Disable TOO LONG
        '--disable=broad-exception-caught',         # Disable BROAD exception
        '--disable=broad-exception-raised',         # Disable BROAD exception
        '--disable=too-many-return-statements',     # :D I don't think so :D
        '--disable=too-many-branches'               # :D I don't think so :D
    ]
    if file_name in ['Tasks.py', 'microIO.py', 'Types.py']:
        pylint_opts.append('--disable=exec-used')   # Disable micrOS execution core exec/eval warning
        pylint_opts.append('--disable=eval-used')
    # Run pylint on the specified file
    results = Run([file_path] + pylint_opts, exit=False)

    # Access the results
    score = round(results.linter.stats.global_note, 2)
    #msg_stat = results.linter.msg_status
    issues = results.linter.linter.stats.by_msg
    return score, issues


def run_pylint(categories, verbose=True, dry_run=False):
    # ERROR CONFIG: drop error if this is in pylint output
    error_msg_core = ['syntax-error', 'undefined-variable', 'bad-indentation']  # 'no-member' ?
    # BYPASS 'no-member' due to duty and sleep_ms micropython functions is drops false alarm, etc.
    error_msg_lm = ['syntax-error', 'undefined-variable']

    avg_core_score = 0
    avg_lm_score = 0
    core_code = categories['core']
    lm_code = categories['load_module']

    for code in core_code:
        if code == 'linter' or dry_run:
            continue
        core_score, core_issue = _run_pylint(code)
        avg_core_score += core_score
        source_is_ok = not any(key in core_issue for key in error_msg_core)
        categories['core'][code]['linter']['pylint'] = (core_score, core_issue, source_is_ok)
    for code in lm_code:
        if code == 'linter' or dry_run:
            continue
        lm_score, lm_issue = _run_pylint(code)
        avg_lm_score += lm_score
        source_is_ok = not any(key in lm_issue for key in error_msg_lm)
        categories['load_module'][code]['linter']['pylint'] = (lm_score, lm_issue, source_is_ok)

    avg_core_score = round(avg_core_score / (len(core_code)-1), 2)
    categories['core']['linter']['pylint'] = avg_core_score
    avg_lm_score = round(avg_lm_score / (len(lm_code)-1), 2)
    categories['load_module']['linter']['pylint'] = avg_lm_score
    if verbose:
        print(f"{'_'*100}\nRUN run_pylint")
        print(json.dumps(categories, sort_keys=True, indent=4))
    return categories


def pylint_verdict_analyze(categories):
    state = True
    failed = []
    core = categories['core']
    lm = categories['load_module']
    resources = {**lm, **core}
    for res in resources:
        if 'linter' in res:
            continue
        try:
            is_ok = resources[res]['linter']['pylint'][2]
        except Exception as e:
            print(f"pylint_verdict_analyze error: missing key:{e} in [{res}] {resources[res]['linter']}")
            is_ok = False
        if not is_ok:
            failed.append(res)
        state &= is_ok
    return state, failed

def add_ref_counter(categories, verbose=True):
    def _update(_m_keys, _dep, _res):
        nonlocal categories
        for _m_key in _m_keys:
            try:
                if categories[_m_key][_dep]['linter'].get('ref', None) is None:
                    categories[_m_key][_dep]['linter']['ref'] = [0, []]
                categories[_m_key][_dep]['linter']['ref'][0] += 1
                categories[_m_key][_dep]['linter']['ref'][1].append(_res)
                if verbose:
                    print(f"\tUpdate refs: {_m_key}->{_dep}->linter:")
                    print(json.dumps(categories[_m_key][_dep]['linter'], sort_keys=True, indent=4))
                return True
            except Exception as e:
                print(f"ERROR: add_ref_counter {_m_key}->{_dep}: {e}: ")
        return False

    for master_key in categories:
        # Skip master keys
        if master_key in ['pin_maps', 'other']:
            continue
        for res in categories[master_key]:
            if 'linter' == res:
                continue
            dep_list = categories[master_key][res]['dependencies']['core'] + \
                       categories[master_key][res]['dependencies']['lm']
            if len(dep_list) == 0:
                continue
            for dep in dep_list:
                dep = f'{dep}.py'
                _update(_m_keys=['core', 'load_module'], _dep=dep, _res=res)
    if verbose:
        print(f"{'_'*100}\nRUN add_ref_counter")
        print(json.dumps(categories, sort_keys=True, indent=4))
    return categories


def _verdict_gen(master_key, categories, verbose=True):
    long_verdict = []
    short_result = {}
    def _spacer(_word, next_col=25):
        return ' ' * (next_col - len(_word))

    for i, master_module in enumerate(categories[master_key]):
        if 'linter' != master_module:
            lines = categories[master_key][master_module]['linter']['lines']
            try:
                ref = categories[master_key][master_module]['linter']['ref']
            except:
                ref = [0, []]
                if master_module == 'core':
                    ref = ['?', []]
            spacer = "\n" + " " * 98
            ref_verdict = f'{ref[0]}:{spacer.join(ref[1])}' if verbose else ref[0]
            if isinstance(ref_verdict, int):
                ref_cnt = f"{Colors.BOLD}{ref_verdict}{Colors.NC}" if ref_verdict > 0 else ref_verdict
            else:
                ref_cnt = ref_verdict

            mlint = categories[master_key][master_module]['linter']['mlint'][0]
            mlint = f"{Colors.OK}OK{Colors.NC}" if mlint else f"{Colors.WARN}NOK{Colors.NC}"
            try:
                pylint = categories[master_key][master_module]['linter']['pylint'][0]
            except Exception as e:
                pylint = f'{e}'
            long_verdict.append(f"\t{i+1}\t{lines}\t{master_module}{_spacer(master_module)}(mlint: {mlint})\t(pylint: {pylint})\t(ref.: {ref_cnt})")
            short_result[master_module] = [pylint, ref_verdict]
    return  short_result, long_verdict


def check_while_out_of_async_in_load_modules():
    # TODO...
    pass


def create_summary_stat(categories, states, verbose=True):
    summary = {'files': {}, 'summary': {'core': ['<lines>', '<files>'], 'load': ['<lines>', '<files>'],
                                    'core_dep': [True, '<warning_cnt(s)>'], 'load_dep': [True, '<warning_cnt(s)>'],
                                    'core_score': 0, 'load_score': 0, 'version': 0}}

    try:
        summary['summary']['version'] = Compile().get_micros_version_from_repo()
    except Exception as e:
        print(f"GET micrOS repo version error: {e}")
    # Get CORE code lines (0), and CORE code files number
    summary['summary']['core'] = [categories['core']['linter']['sum_lines'], len(categories['core'])-1]
    # Get LM code lines (0), and LM code files number
    summary['summary']['load'] = [categories['load_module']['linter']['sum_lines'], len(categories['load_module'])-1]

    # GET CORE micrOS lint verdict (bool, warnings) + extend categories
    core_dep = states.get('core_dep_checker')
    categories['core']['linter']['mlint'] = core_dep
    summary['summary']['core_dep'] = [core_dep[0], core_dep[1]]

    # GET LM micrOS lint verdict (bool, warnings)  + extend categories
    lm_dep = states.get('load_module_checker')
    categories['load_module']['linter']['mlint'] = lm_dep
    summary['summary']['load_dep'] = [lm_dep[0], lm_dep[1]]

    # GET CORE overall score
    summary['summary']['core_score'] = categories['core']['linter']['pylint']
    # GET LM overall score
    summary['summary']['load_score'] = categories['load_module']['linter']['pylint']

    if verbose:
        print(f"{'_'*100}\nRUN create_summary_stat")
        print(json.dumps(summary, sort_keys=True, indent=4))
    return categories, summary


def short_report(categories, states, verbose=True):
    c_OK = f'{Colors.OK}OK{Colors.NC}'
    c_NOK = f'{Colors.ERR}NOK{Colors.NC}'
    def _vis(data):
        if data > 0:
            return f'({Colors.WARN}+{round(data, 1)}{Colors.NC})'
        elif data < 0:
            return f"({Colors.WARN}{round(data, 1)}{Colors.NC})"
        else:
            return ''
    def _pyl_vis(data):
        if data > 0:
            return f'({Colors.OK}+{round(data, 1)}{Colors.NC})'
        elif data < 0:
            return f"({Colors.ERR}{round(data, 1)}{Colors.NC})"
        else:
            return ''

    # Create summary stat
    categories, summary = create_summary_stat(categories, states, verbose=True)
    # Unpack result of summary stat
    sum_core_lines, core_cnt = summary['summary']['core'][0], summary['summary']['core'][1]
    sum_lm_lines, lm_cnt = summary['summary']['load'][0], summary['summary']['load'][1]
    core_dep = summary['summary']['core_dep']
    lm_dep = summary['summary']['load_dep']
    core_pylint = summary['summary']['core_score']
    lm_pylint = summary['summary']['load_score']
    pylint_check = states.get('pylint_checker')

    # CORE and LM verdict generation
    summary['files'], printout1 = _verdict_gen(master_key='core', categories=categories, verbose=verbose)
    _files, printout2 = _verdict_gen(master_key='load_module', categories=categories, verbose=verbose)
    summary['files'].update(_files)

    # Generate summary DIFF
    try:
        summary_diff, is_better = diff_short_summary(summary, verbose=True)
        core_diff = summary_diff['summary']['core']
        load_diff = summary_diff['summary']['load']
        core_score_diff = summary_diff['summary']['core_score']
        load_score_diff = summary_diff['summary']['load_score']
        core_dep_diff = summary_diff['summary']['core_dep'][1]
        lm_dep_diff = summary_diff['summary']['load_dep'][1]
    except Exception as e:
        print(f"\n\ndiff_short_summary error: no file: {e}\n\n")
        is_better = True    # enable save
        core_diff, load_diff, core_score_diff, load_score_diff, core_dep_diff, lm_dep_diff = [0, 0], [0, 0], 0, 0, 0, 0

    if not verbose:
        print(json.dumps(categories, sort_keys=True, indent=4))
    print(f"#####################        {Colors.BOLD}micrOS linter/scripts{Colors.NC}      #######################")
    print(f"#########################            {Colors.UNDERLINE}v{summary['summary']['version']}{Colors.NC}      ###########################")
    print("Core micrOS resources")
    for line in printout1:
        print(line)
    print("micrOS Load Module resources")
    for line in printout2:
        print(line)
    print("########################        micrOS linter      ###########################")
    print(f"        core system:                {sum_core_lines}{_vis(core_diff[0])} lines / {core_cnt}{_vis(core_diff[1])} files")
    print(f"       load modules:                {sum_lm_lines}{_vis(load_diff[1])} lines / {lm_cnt}{_vis(load_diff[1])} files")
    print(f"   core_dep_checker:                core dependency check (no LM): {c_OK if core_dep[0]  else c_NOK} {'' if core_dep[1] == 0 else f'{core_dep[1]}{_vis(core_dep_diff)} warning(s)s'}")
    print(f"load_module_checker:                load module dependency check (no core): {c_OK if lm_dep[0] else c_NOK} {'' if lm_dep[1] == 0 else f'{lm_dep[1]}{_vis(lm_dep_diff)} warning(s)'}")
    print(f"  core pylint score:                {core_pylint}{_pyl_vis(core_score_diff)}")
    print(f"load module pylint score:           {lm_pylint}{_pyl_vis(load_score_diff)}")
    print(f"pylint resource check (syntax?):     {c_OK if pylint_check[0] else f'{c_NOK}: {pylint_check[1]}' }")

    exitcode = sum([1 for k, v in states.items() if not v[0]])
    print(f"micrOSlint verdict: {c_OK if exitcode == 0 else c_NOK}")
    print(f"Exitcode: {exitcode}")
    return exitcode, categories, summary, is_better


def diff_short_summary(summary, verbose=True):
    is_better = False
    diff_summary = {'files': {}, 'summary': {'core': ['<lines>', '<files>'], 'load': ['<lines>', '<files>'],
                                    'core_dep': [True, '<warning_cnt(s)>'], 'load_dep': [True, '<warning_cnt(s)>'],
                                    'core_score': 0, 'load_score': 0, 'version': 0}}
    file_path = os.path.join(RELEASE_INFO_PATH, 'system_analysis_sum.json')
    try:
        with open(file_path, 'r') as json_file:
            stored_summary = json.loads(json_file.read())
    except:
        print("NO stored summary to compare system_analysis_sum.json")
        return
    for f_name, data in summary['files'].items():
        score, ref = data[0], data[1]
        diff_summary['files'][f_name] = [score - stored_summary['files'][f_name][0], ref - stored_summary['files'][f_name][1]]
    for tag, data in summary['summary'].items():
        if isinstance(data, int) or isinstance(data, float):
            diff_summary['summary'][tag] = data - stored_summary['summary'][tag]
            is_better |= False if diff_summary['summary'][tag] < 0 else True
        if isinstance(data, list):
            for i, d in enumerate(data):
                if isinstance(d, int) or isinstance(d, float):
                    diff_summary['summary'][tag][i] = d - stored_summary['summary'][tag][i]
                    is_better |= False if diff_summary['summary'][tag][i] < 0 else True
    if verbose:
        print(f"{'_'*100}\nRUN diff_short_summary")
        print(json.dumps(diff_summary, sort_keys=True, indent=4))
    return diff_summary, is_better


def save_system_analysis_json(categories):
    file_path = os.path.join(MYPATH, 'user_data/system_analysis.json')
    sorted_categories = {key: categories[key] for key in sorted(categories)}
    with open(file_path, 'w') as json_file:
        json.dump(sorted_categories, json_file, indent=4)
    return f"system_analysis json saved to {file_path}"

def save_system_summary_json(summary):
    file_path = os.path.join(RELEASE_INFO_PATH, 'system_analysis_sum.json')
    with open(file_path, 'w') as json_file:
        json.dump(summary, json_file, indent=4)
    return f"system_analysis summary json saved to {file_path}"


def main(verbose=True):
    print(f"Analyze project: {MICROS_SOURCE_DIR}")
    resources = parse_micros_file_categories(verbose=verbose)
    core_struct = parse_core_modules(resources['core'], verbose=verbose)
    lm_struct = parse_core_modules(resources['load_module'], verbose=verbose)
    categories = combine_data_structures(core_struct, lm_struct, all_struct=resources, verbose=verbose)

    print("== RUN checker on parsed resources ==")
    s1, warn1, categories = core_dep_checker(categories, verbose=verbose)
    categories['core']['linter']['mlint'] = (s1, warn1)
    s2, warn2, categories = load_module_checker(categories, verbose=verbose)
    categories['load_module']['linter']['mlint'] = (s1, warn2)
    categories = run_pylint(categories, verbose=verbose, dry_run=False)
    s3, pylint_verdict = pylint_verdict_analyze(categories)
    categories = add_ref_counter(categories, verbose=verbose)

    # Short report
    exitcode, categories, summary, is_better = short_report(categories, {'core_dep_checker': (s1, warn1),
                                                     'load_module_checker': (s2, warn2),
                                                     'pylint_checker': (s3, pylint_verdict)},
                                        verbose=verbose)
    # Archive system_analysis_json
    print(save_system_analysis_json(categories))
    if is_better:
        print(save_system_summary_json(summary))
    return exitcode

if __name__ == "__main__":
    sys.exit(main(verbose=True))

