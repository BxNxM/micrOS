import sys
import os
import subprocess
MYPATH = os.path.dirname(__file__)
USER_DATA_OPT_INST_DONE = os.path.join(MYPATH, '../user_data/.opt_dep_install')
INTERPRETER = sys.executable

sys.path.append(os.path.join(MYPATH, '../'))
from DevEnvCompile import Compile

try:
    from . import TerminalColors
except Exception as e:
    print("Import warning __name__:{}: {}".format(__name__, e))
    import TerminalColors

AVAILABLE_PACKAGES = []

def venv_python_path(venv_path):
    if sys.platform.startswith("win"):
        return os.path.join(venv_path, "Scripts", "python.exe")
    return os.path.join(venv_path, "bin", "python")


def resolve_virtualenv_interpreter():
    active_venv = os.environ.get("VIRTUAL_ENV", None)
    if active_venv:
        python_path = venv_python_path(active_venv)
        if os.path.isfile(python_path):
            print(f"[PIP] Active virtualenv detected: {active_venv}")
            return python_path

    venv_optional = os.path.abspath(os.path.join(MYPATH, '..', 'venv_optional'))
    python_path = venv_python_path(venv_optional)
    if not os.path.isdir(venv_optional):
        print(f"[PIP] Creating optional virtualenv: {venv_optional}")
        run_subprocess([sys.executable, '-m', 'venv', venv_optional])
    if os.path.isfile(python_path):
        print(f"[PIP] Using optional virtualenv: {venv_optional}")
        return python_path

    print("[PIP][SKIP] No virtualenv detected. Create one via: source magic.bash env")
    return None


def compare_versions():
    print("[PIP] OPT INSTALL AUTO TRIGGER - VERSION COMPARE")
    current_micros_version = Compile().get_micros_version_from_repo().strip()
    last_stored_micros_version = None
    if os.path.isfile(USER_DATA_OPT_INST_DONE):
        with open(USER_DATA_OPT_INST_DONE, 'r') as f:
            last_version = f.read()
        last_stored_micros_version = last_version.strip() if '.' in last_version else '0.0.0-0'
    print(f"\t[PIP] repo: {current_micros_version} vs. last: {last_stored_micros_version}")
    if current_micros_version == last_stored_micros_version:
        return True
    return False


def list_packages():
    global AVAILABLE_PACKAGES
    if len(AVAILABLE_PACKAGES) == 0:
        print("[PIP] load available package list")
        output = subprocess.check_output([INTERPRETER, '-m', 'pip', 'list'])
        AVAILABLE_PACKAGES  = [p.strip().split()[0].strip() for p in output.decode('utf-8').split('\n') if '.' in p]
    return AVAILABLE_PACKAGES


def run_subprocess(cmd_list: list):
    try:
        result = subprocess.run(
            cmd_list,
            capture_output=True,  # Captures stdout and stderr
            text=True,  # Decodes output into strings
            check=True  # Raises CalledProcessError for non-zero exit codes
        )
        print(f"Subprocess output: {result.stdout}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"{TerminalColors.Colors.ERR}Subprocess error:{TerminalColors.Colors.NC} {e.stderr}")
        return False, e.stderr

def install_package(name, additional_pip_param=None):
    print(f"Install optional dependency (pip): {name}")
    try:
        if additional_pip_param is None:
            state, out = run_subprocess([INTERPRETER, '-m', 'pip', 'install', name])
        else:
            state, out = run_subprocess([INTERPRETER, '-m', 'pip', 'install', name, additional_pip_param])
        if state:
            print(f"{TerminalColors.Colors.OK}[PIP] install {name} OK{TerminalColors.Colors.NC}")
        else:
            print(f"{TerminalColors.Colors.WARN}[PIP] install {name} NOK{TerminalColors.Colors.NC}")
            if "--break-system-packages" in out:
                # (Retry) Support system wide package install
                install_package(name, additional_pip_param="--break-system-packages")
            elif "This environment is externally managed" in out:
                # (Retry-Fallback) Support brew installed python
                if "brew install" in out:
                    print(f"Install optional dependency (brew): {name}")
                    state, out = run_subprocess(["brew", "install", name])
    except subprocess.CalledProcessError as e:
        print(f"{TerminalColors.Colors.ERR}[PIP] error: {e}{TerminalColors.Colors.NC}")
        state = False
    return state


def install_optional_dependencies(requirements):
    print("[PIP] micrOS optional dependency installer")

    global INTERPRETER
    venv_interpreter = resolve_virtualenv_interpreter()
    if venv_interpreter is None:
        return True
    INTERPRETER = venv_interpreter

    # SKIP if it was already done
    if compare_versions():
        print(f"[PIP] Already (attempted) to install optional dependencies in this version: {USER_DATA_OPT_INST_DONE}")
        return True

    # INSTALL DEPs
    available_packages = list_packages()
    if isinstance(requirements, list):
        for dep in requirements:
            dep_name = dep.split('==')[0] if '==' in dep else dep
            if dep_name not in available_packages:
                install_package(dep)
            else:
                print(f"[PIP] SKIP install {dep} (available)")
        with open(USER_DATA_OPT_INST_DONE, 'w') as f:
            f.write(Compile().get_micros_version_from_repo().strip())
        return True
    return False


if __name__ == "__main__":
    print(list_packages())
    install_optional_dependencies(['PyQt5'])
