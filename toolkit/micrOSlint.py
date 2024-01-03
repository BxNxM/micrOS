import os
import json
import sys
from pylint.lint import Run

try:
    from .lib import LocalMachine
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    from lib import LocalMachine

MYPATH = os.path.dirname(__file__)
MICROS_SOURCE_DIR = os.path.join(MYPATH, '../micrOS/source')


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
        elif f.startswith('LP_') and f.endswith('.py'):
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
        if len(raw_line) > 0:
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
        line_cnt, dependencies = _parse_py_file_content(file_name, verbose=False)
        core_resource_struct[file_name] = {'lines': line_cnt, 'dependencies': dependencies}
    if verbose:
        print("RUN parse_core_modules")
        #print(json.dumps(core_resource_struct, sort_keys=True, indent=4))
        print(core_resource_struct)
    return core_resource_struct


def parse_load_modules(lm_resources, verbose=True):
    lm_resource_struct = {}
    for file_name in lm_resources:
        line_cnt, dependencies = _parse_py_file_content(file_name, verbose=False)
        lm_resource_struct[file_name] = {'lines': line_cnt, 'dependencies': dependencies}
    if verbose:
        print("RUN parse_load_modules")
        #print(json.dumps(lm_resource_struct, sort_keys=True, indent=4))
        print(lm_resource_struct)
    return lm_resource_struct


def _update_dep_category(struct, core_filter_list, lm_filter_list, master_key='core'):
    categories = {master_key: {}}
    lines_sum = 0
    for core in struct:
        core_module_dep = struct[core]['dependencies']
        lines = struct[core]['lines']
        lines_sum += lines
        for mod_dep in core_module_dep:
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
            # Filter core resources
            if mod_dep in core_filter_list:
                categories[master_key][core]['dependencies']['core'].append(mod_dep)
            elif mod_dep in lm_filter_list:
                # Filter lm resources
                categories[master_key][core]['dependencies']['lm'].append(mod_dep)
            else:
                categories[master_key][core]['dependencies']['builtin'].append(mod_dep)
        categories[master_key][core]['linter']['lines'] = lines
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
        print("RUN combine_data_structures")
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
        print(f"RUN core_dep_checker ({state})")
        print(json.dumps(verdict, sort_keys=True, indent=4))

    core_dep_warnings = sum([1 for v in verdict if not v[1]])
    return state, f'{core_dep_warnings} warning(s)', categories


def load_module_checker(categories, verbose=True):

    def _is_allowed(_relation):
        _allowed_core_resources = ['Common', 'LogicalPins']
        _to_remove = []
        for _allow in _relation:
            if _allow in _allowed_core_resources:
                _to_remove.append(_allow)
        for rm in _to_remove:
            _relation.remove(rm)
        return _relation

    lm_god_mode = ['LM_system.py', 'LM_lmpacman.py', 'LM_intercon.py']
    state_lm_dep = True
    verdict = []
    lm_resources = categories['load_module']
    for lm_res in lm_resources:
        try:
            categories['load_module'][lm_res]['linter']['mlint'] = (True, 'OK')
            core_relation = lm_resources[lm_res]['dependencies']['core']
            core_relation = _is_allowed(core_relation)
            if len(core_relation) > 0:
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
    if lm_dep_warnings <= 7:  # Temporary fix, drops error if quality pattern goes down...
        # TODO: After fixes it can be set as False in this case, if it make sense
        state_lm_dep = True
    if verbose or not state_lm_dep:
        print(f"RUN load_module_checker ({state_lm_dep})")
        print(json.dumps(verdict, sort_keys=True, indent=4))
    return state_lm_dep, f'{lm_dep_warnings} warning(s)', categories


def _run_pylint(file_name):
    file_path = os.path.join(MICROS_SOURCE_DIR, file_name)
    # Customize pylint options
    pylint_opts = [
        '--disable=import-error',                   # Ignore import error due to micropython deps
        '--disable=missing-class-docstring',        # Disable DOCSTRING: class
        '--disable=missing-function-docstring',     # Disable DOCSTRING: function
        '--disable=line-too-long',                  # Disable TOO LONG
        '--disable=broad-exception-caught',         # Disable BROAD exception
        '--disable=broad-exception-raised'          # Disable BROAD exception
    ]
    # Run pylint on the specified file
    results = Run([file_path] + pylint_opts, exit=False)

    # Access the results
    score = round(results.linter.stats.global_note, 2)
    #msg_stat = results.linter.msg_status
    issues = results.linter.linter.stats.by_msg
    return score, issues


def run_pylint(categories, verbose=True, dry_run=False):
    error_messages = ['syntax-error', 'undefined-variable']         # drop error if this is in pylint output
    avg_core_score = 0
    avg_lm_score = 0
    core_code = categories['core']
    lm_code = categories['load_module']

    for code in core_code:
        if code == 'linter' or dry_run:
            continue
        core_score, core_issue = _run_pylint(code)
        avg_core_score += core_score
        source_is_ok = not any(key in core_issue for key in error_messages)
        categories['core'][code]['linter']['pylint'] = (core_score, core_issue, source_is_ok)
    for code in lm_code:
        if code == 'linter' or dry_run:
            continue
        lm_score, lm_issue = _run_pylint(code)
        avg_lm_score += lm_score
        source_is_ok = not any(key in lm_issue for key in error_messages)
        categories['load_module'][code]['linter']['pylint'] = (lm_score, lm_issue, source_is_ok)

    avg_core_score = round(avg_core_score / (len(core_code)-1), 2)
    categories['core']['linter']['pylint'] = avg_core_score
    avg_lm_score = round(avg_lm_score / (len(lm_code)-1), 2)
    categories['load_module']['linter']['pylint'] = avg_lm_score
    if verbose:
        print(f"RUN run_pylint")
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
                    print(f"\tUpdate refs: {_m_key}->{_dep}->linter: {categories[_m_key][_dep]['linter']}")
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
            print(f"||{master_key}-{res} Lm&core:{dep_list}||")
            if len(dep_list) == 0:
                continue
            for dep in dep_list:
                dep = f'{dep}.py'
                print(f"+++> UPDATE: {master_key}-{res}")
                _update(_m_keys=['core', 'load_module'], _dep=dep, _res=res)
    if verbose:
        print(f"RUN add_ref_counter")
        #print(json.dumps(categories, sort_keys=True, indent=4))
    return categories


def short_report(categories, states, verbose=False):

    def _spacer(_word, next_col=25):
        return ' ' * (next_col - len(_word))


    sum_core_lines, core_cnt = categories['core']['linter']['sum_lines'], len(categories['core'])-1
    sum_lm_lines, lm_cnt = categories['load_module']['linter']['sum_lines'], len(categories['load_module'])-1

    core_dep = states.get('core_dep_checker')
    categories['core']['linter']['mlint'] = core_dep
    lm_dep = states.get('load_module_checker')
    categories['load_module']['linter']['mlint'] = lm_dep
    core_pylint = categories['core']['linter']['pylint']
    lm_pylint = categories['load_module']['linter']['pylint']
    pylint_check = states.get('pylint_checker')

    #print(json.dumps(categories, sort_keys=True, indent=4))
    print("#####################        micrOS linter/scripts      #######################")
    print("Core micrOS resources")
    for i, core_module in enumerate(categories['core']):
        if 'linter' != core_module:
            lines = categories['core'][core_module]['linter']['lines']
            try:
                ref = categories['core'][core_module]['linter']['ref']
            except:
                ref = ['?', []]
            mlint = categories['core'][core_module]['linter']['mlint'][0]
            try:
                pylint = categories['core'][core_module]['linter']['pylint'][0]
            except Exception as e:
                pylint = f'{e}'
            print(f"\t{i+1}\t{lines}\t{core_module}{_spacer(core_module)}(mlint: {mlint})\t(pylint: {pylint})\t(ref.: {ref if verbose else ref[0]})")
    print("micrOS Load Module resources")
    for i, lm_module in enumerate(categories['load_module']):
        if 'linter' != lm_module:
            lines = categories['load_module'][lm_module]['linter']['lines']
            try:
                ref = categories['load_module'][lm_module]['linter']['ref']
            except:
                ref = [0, []]
            mlint = categories['load_module'][lm_module]['linter']['mlint'][0]
            try:
                pylint = categories['load_module'][lm_module]['linter']['pylint'][0]
            except Exception as e:
                pylint = f'{e}'
            print(f"\t{i+1}\t{lines}\t{lm_module}{_spacer(lm_module)}(mlint: {mlint})\t(pylint: {pylint})\t(ref.: {ref if verbose else ref[0]})")
    print("########################        micrOS linter      ###########################")
    print(f"        core system:                {sum_core_lines} lines / {core_cnt} files")
    print(f"       load modules:                {sum_lm_lines} lines / {lm_cnt} files")
    print(f"   core_dep_checker:                core dependency check (no LM): {core_dep}")
    print(f"load_module_checker:                load module dependency check (no core): {lm_dep}")
    print(f"  core pylint score:                {core_pylint}")
    print(f"load module pylint score:           {lm_pylint}")
    print(f"pylint resource check (syntax):     {pylint_check}")


    exitcode = sum([1 for k, v in states.items() if not v[0]])
    print(f"micrOSlint verdict: {'OK' if exitcode == 0 else 'NOK'} Exitcode: {exitcode}")
    return exitcode, categories

def save_system_analysis_json(categories):
    file_path = os.path.join(MYPATH, 'user_data/system_analysis.json')
    with open(file_path, 'w') as json_file:
        json.dump(categories, json_file, indent=4)
    return f"system_analysis json saved to {file_path}"

def main(verbose=True):
    print(f"Analyze project: {MICROS_SOURCE_DIR}")
    resources = parse_micros_file_categories(verbose=verbose)
    core_struct = parse_core_modules(resources['core'], verbose=verbose)
    lm_struct = parse_core_modules(resources['load_module'], verbose=verbose)
    categories = combine_data_structures(core_struct, lm_struct, all_struct=resources, verbose=verbose)

    print("== RUN checker on parsed resources ==")
    s1, text1, categories = core_dep_checker(categories, verbose=verbose)
    categories['core']['linter']['mlint'] = (s1, text1)
    s2, text2, categories = load_module_checker(categories, verbose=verbose)
    categories['load_module']['linter']['mlint'] = (s1, text1)
    categories = run_pylint(categories, verbose=verbose, dry_run=False)
    s3, pylint_verdict = pylint_verdict_analyze(categories)
    categories = add_ref_counter(categories, verbose=verbose)

    # Short report
    exitcode, categories = short_report(categories, {'core_dep_checker': (s1, text1),
                                                     'load_module_checker': (s2, text2),
                                                     'pylint_checker': (s3, pylint_verdict)},
                                        verbose=verbose)
    # Archive system_analysis_json
    print(save_system_analysis_json(categories))
    return exitcode

if __name__ == "__main__":
    sys.exit(main(verbose=False))

