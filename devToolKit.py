#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os


if len(sys.argv) > 1 and sys.argv[1] in ['light', '--light']:
    print('LIGHT DEPLOYMENT: skip optional dependencies')
    sys.argv.remove(sys.argv[1])
else:
    # INSTALL OPTIONAL DEPENDENCIES - PIP HACK
    from toolkit.lib import pip_package_installer as pip_install
    pip_install.install_optional_dependencies(['PyQt5', 'opencv-python', 'PyAudio', 'mpy-cross==1.24.1.post2', 'matplotlib'])
    if sys.platform.startswith("win"):
        pip_install.install_optional_dependencies(['pyreadline3'])

# NORMAL CODE ...
MYPATH = os.path.dirname(__file__)
print("Module [devToolKit] path: {} __package__: {} __name__: {} __file__: {}".format(
    sys.path[0], __package__, __name__, MYPATH))

TOOLKIT_PATH = os.path.join(MYPATH, 'toolkit')
APP_DIR = os.path.join(MYPATH, 'toolkit/dashboard_apps')
import argparse
from toolkit import MicrOSDevEnv
from toolkit import socketClient
from toolkit.lib import LocalMachine
try:
    from toolkit import micrOSlint
except Exception as e:
    print(f"micrOS linter import error: {e}")
    micrOSlint = None
try:
    from toolkit.lib import macroScript
except Exception as e:
    print(f"Optional dependency missing in macroScript: {e}")
    macroScript = None
try:
    from toolkit.WebRepl import open_webrepl
except Exception as e:
    print(f"Optional dependency missing in WebRepl: {e}")
    open_webrepl = None


def arg_parse():
    parser = argparse.ArgumentParser(prog="micrOS dev toolkit - deploy, connect, update, etc.",
                                            description="CMDline wrapper for {}\n and for {}\n[HINTS] USED ENV VARS FOR GATEWAY:\n API_AUTH=usr:pwd, GATEWAYIP=10.0.1.1, MACRO_WORKDIR=~/macros".format(
                                            os.path.join(TOOLKIT_PATH, 'MicrOSDevEnv.py'),
                                            os.path.join(TOOLKIT_PATH, 'socketClient.py')))

    base_group = parser.add_argument_group("Base commands")
    base_group.add_argument("-pupdate", "--pip_update", action="store_true", help="Update micrOS devToolKit (pip) package - app")
    base_group.add_argument("-m", "--make", action="store_true", help="Erase & Deploy & Precompile (micrOS) & Install (micrOS)")
    base_group.add_argument("-r", "--update", action="store_true", help="Update/redeploy connected (usb) micrOS. - node config will be restored")
    base_group.add_argument("-s", "--search_devices", action="store_true", help="Search devices on connected wifi network.")
    base_group.add_argument("-o", "--OTA", action="store_true", help="OTA (OverTheArir update with webrepl)")
    base_group.add_argument("-c", "--connect", action="store_true", help="Connect via socketclinet")
    base_group.add_argument("-p", "--connect_parameters", type=str, help="Parameters for connection in non-interactive mode. For more info: -p 'help'")
    base_group.add_argument("-a", "--applications", type=str, help="List/Execute frontend applications. [list]")
    base_group.add_argument("-macro", "--macro", type=str, help="Run micrOS remote command sequence from .macro file. If file not exists creates a template")
    base_group.add_argument("-stat", "--node_status", action="store_true", help="Show all available micrOS devices status data.")
    base_group.add_argument("-cl", "--clean", action="store_true", help="Clean user connection data: device_conn_cache.json")

    dev_group = parser.add_argument_group("Development & Deployment & Connection")
    dev_group.add_argument("-f", "--force_update", action="store_true", help="Force mode for -r/--update and -o/--OTA")
    dev_group.add_argument("-e", "--erase", action="store_true", help="Erase device")
    dev_group.add_argument("-d", "--deploy", action="store_true", help="Deploy micropython binary (image) over usb. After this, python interpreter will be available on the board.")
    dev_group.add_argument("-i", "--install", action="store_true", help="Install micrOS on micropython, copy all micrOS code to the board after micropython was installed.")
    dev_group.add_argument("-l", "--list_devs_n_bins", action="store_true", help="List connected devices & micropython binaries.")
    dev_group.add_argument("-ls", "--node_ls", action="store_true", help="List micrOS node filesystem content.")
    dev_group.add_argument("-u", "--connect_via_usb", action="store_true", help="Connect via serial port - usb")
    dev_group.add_argument("-b", "--backup_node_config", action="store_true", help="Backup usb connected node config.")
    dev_group.add_argument("-sim", "--simulate", action="store_true", help="start micrOS on your computer in simulated mode")
    dev_group.add_argument("-cc", "--cross_compile_micros", action="store_true", help="Cross Compile micrOS system [py -> mpy], MICROS_DEV env. var: enable compile-> True (disabled for pip deployments)")
    dev_group.add_argument("-gw", "--gateway", action="store_true", help="Start micrOS Gateway rest-api server, Env. vars: API_AUTH='username:password' (optional), GATEWAYIP needed for container deployment only.")
    dev_group.add_argument("-v", "--version", action="store_true", help="Get micrOS version - repo + connected device.")
    dev_group.add_argument("-lint", "--linter", action="store_true", help="Run micrOS system linter (pylint+)")
    dev_group.add_argument("-webrepl", "--open_webrepl", action="store_true", help="(beta) Open webrepl in default browser, micropython repl + file transfers (built-in)")
    dev_group.add_argument("--light", action="store_true", help="Skip optional dependency deployments (low level param: add this as first argument always)")

    toolkit_group = parser.add_argument_group("Toolkit development")
    toolkit_group.add_argument("--dummy", action="store_true", help="Skip subshell executions - for API logic test.")
    args = parser.parse_args()
    return args


def list_devs_n_bins(api_obj):
    dev_list = api_obj.get_devices()
    bin_list = api_obj.get_micropython_binaries()
    print("Devices:")
    for dev in dev_list:
        print("\t{}".format(dev))
    print("Micropython binaries:")
    for bin_ in bin_list:
        print("\t{}".format(bin_))


def make(api_obj):
    api_obj.deploy_micros()


def erase(api_obj):
    api_obj.erase_dev()


def deploy(api_obj):
    api_obj.deploy_micropython_dev()


def install(api_obj):
    api_obj.put_micros_to_dev()


def connect(args=None):
    if args is not None and len(args) != 0:
        arg_list = args.split()
        socketClient.run(arg_list=arg_list)
    else:
        socketClient.run(arg_list=[])


def ota_update(api_obj, force=False):
    api_obj.update_with_webrepl(force=force)


def node_status():
    socketClient.run(arg_list=['--stat'])


def clean_user_data():
    socketClient.run(arg_list=['--clean'])


def search_devices():
    socketClient.ConnectionData.search_micrOS_on_wlan()


def precompile_micrOS(api_obj):
    if api_obj.precompile_micros():
        return "Precompile OK"
    return "Precompile NOK"


def connect_via_usb(api_obj):
    api_obj.connect_dev()


def get_MicrOS_version(api_obj):
    print(api_obj.get_micrOS_version())


def update_micrOS_on_node(api_obj, force=False):
    api_obj.update_micros_via_usb(force=force)


def node_ls(api_obj):
    api_obj.list_micros_filesystem()


def backup_node_config(api_obj):
    api_obj.backup_node_config()


def simulate_micrOS(api_obj):
    api_obj.simulator()


def gateway_rest_api():
    from toolkit import Gateway
    Gateway.gateway(debug=False)


def applications(api_obj, app):
    print(APP_DIR)
    app_list = [app for app in LocalMachine.FileHandler.list_dir(APP_DIR) if app.endswith('.py') and not app.startswith('Template')]
    if app.lower() == 'list' or app.lower() == 'help' or app.lower() == '-':
        for index, app_content in enumerate(app_list):
            print("\t[{index}] - {appc}".format(index=index, appc=app_content))
        index = input("[QUESTION] Select Appllication by index: ")
        try:
            index = int(index)
            app_name = app_list[index].replace('_app.py', '')
        except:
            app_name = None
        if app_name is not None:
            __execute_app(api_obj, app_name)
    elif app in [app_name.replace('_app.py', '') for app_name in app_list]:
        print("[ RUN ] {}".format(app))
        __execute_app(api_obj, app)
    else:
        print("[ APP ] {} was not found.".format(app))


def __execute_app(api_obj, app_name):
    dev_name = "__simulator__"

    print(api_obj.exec_app(app_name, dev_name))


def init_gui(cmdargs):
    if len(sys.argv) == 1 or cmdargs.pip_update:
        from toolkit import micrOSdashboard
        print("Init GUI")
        micrOSdashboard.main()


def update_pip_package():
    print("[PIP] Check package update and update")
    import subprocess
    try:
        # Update the package using pip
        out = subprocess.check_call(['pip', 'install', '--upgrade', 'micrOSDevToolKit'])
    except Exception as e:
        print("ERROR update_pip_package: {}".format(e))
        out = 1
    return True if out == 0 else False


if __name__ == "__main__":
    # Arg parse
    cmd_args = arg_parse()

    # Check update
    if cmd_args.pip_update:
        update_pip_package()

    # Init GUI
    init_gui(cmd_args)

    # Socket interface module
    if cmd_args.connect:
        connect(args=cmd_args.connect_parameters)
        sys.exit(0)

    if cmd_args.clean:
        clean_user_data()

    if cmd_args.search_devices:
        search_devices()

    # Get all connected node status
    if cmd_args.node_status:
        node_status()

    # Create API object ()
    if cmd_args.dummy:
        api_obj = MicrOSDevEnv.MicrOSDevTool(dummy_exec=True)
    else:
        api_obj = MicrOSDevEnv.MicrOSDevTool()

    if cmd_args.simulate:
        simulate_micrOS(api_obj)

    if cmd_args.applications:
        applications(api_obj, cmd_args.applications)
        sys.exit(0)

    # Commands
    if cmd_args.OTA:
        ota_update(api_obj, force=cmd_args.force_update)

    if cmd_args.list_devs_n_bins:
        list_devs_n_bins(api_obj)

    if cmd_args.make:
        make(api_obj)

    if cmd_args.erase:
        erase(api_obj)

    if cmd_args.deploy:
        deploy(api_obj)

    if cmd_args.install:
        install(api_obj)

    if cmd_args.cross_compile_micros:
        print(precompile_micrOS(api_obj))

    if cmd_args.version:
        get_MicrOS_version(api_obj)

    if cmd_args.update:
        update_micrOS_on_node(api_obj, force=cmd_args.force_update)

    if cmd_args.node_ls:
        node_ls(api_obj)

    if cmd_args.backup_node_config:
        backup_node_config(api_obj)

    if cmd_args.connect_via_usb:
        connect_via_usb(api_obj)

    if cmd_args.gateway:
        gateway_rest_api()

    if cmd_args.linter:
        if micrOSlint is not None:
            sys.exit(micrOSlint.main(verbose=False))

    if cmd_args.open_webrepl:
        if open_webrepl is not None:
            open_webrepl()

    if cmd_args.macro:
        if macroScript is None:
            print("macroScript not available :(")
        else:
            executor = macroScript.Executor()
            executor.run_micro_script(cmd_args.macro)

    sys.exit(0)
