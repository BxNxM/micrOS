#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import shutil
import signal
import tarfile
import getpass
import fileinput
import subprocess


def debug_print(msg, debug=False):
    if debug:
        print(msg)


class SimplePopPushd:

    def __init__(self):
        self.original_path = None

    def pushd(self, target_path):
        # Save actual path
        self.original_path = os.getcwd()
        if os.path.isdir(target_path):
            print("[PUSHD] change dir {} -> {}".format(self.original_path, target_path))
            os.chdir(target_path)
            return True
        return False

    def popd(self):
        if self.original_path is not None:
            os.chdir(self.original_path)
            print("[POPD] restore original path: {}".format(self.original_path))
            return True
        return False


class FileHandler:
    '''
    Filehandler class contains file and dir related
    functionalities, like:
        * copy
        * move
        * permission handling
        * etc
    '''
    @staticmethod
    def path_is_exists(path):
        type_ = None
        if os.path.exists(path):
            debug_print("{} is exists.".format(path))
            if FileHandler.__path_is_dir(path):
                type_ = "d"
            elif FileHandler.__path_is_file(path):
                type_ = "f"
            elif FileHandler.__path_is_link(path):
                type_ = "l"
            elif FileHandler.__path_is_mount(path):
                type_ = "m"
            else:
                type_ = "?"
            return True, type_
        else:
            debug_print("[DEBUG] {} does not exist.".format(path))
            return False, type_

    @staticmethod
    def __path_is_dir(path):
        if os.path.isdir(path):
            debug_print("[DEBUG] {} is dir.".format(path))
            return True
        else:
            debug_print("[DEBUG] {} not dir.".format(path))
            return False

    @staticmethod
    def __path_is_file(path):
        if os.path.isfile(path):
            debug_print("[DEBUG] {} is file.".format(path))
            return True
        else:
            debug_print("[DEBUG] {} not file.".format(path))
            return False

    @staticmethod
    def __path_is_link(path):
        if os.path.islink(path):
            debug_print("[DEBUG] {} is symbolic link.".format(path))
            return True
        else:
            debug_print("[DEBUG] {} not symbolic link.".format(path))
            return False

    @staticmethod
    def __path_is_mount(path):
        if os.path.ismount(path):
            debug_print("[DEBUG] {} is mount.".format(path))
            return True
        else:
            debug_print("[DEBUG] {} not mount.".format(path))
            return False

    @staticmethod
    def list_dir(path):
        if FileHandler.__path_is_dir(path):
            try:
                return os.listdir(path)
            except os.error:
                return []
        else:
            raise Exception("Path {} is not dir".format(path))

    @staticmethod
    def create_dir(path, recreate=False):
        if recreate and FileHandler.path_is_exists(path)[0]:
            debug_print("[DEBUG] Recreate dir - delete phase")
            shutil.rmtree(path)
        if not FileHandler.path_is_exists(path)[0]:
            debug_print("[DEBUG] Create " + path)
            os.makedirs(path)

    @staticmethod
    def create_symlink(source, link):
        if FileHandler.path_is_exists(source)[0]:
            debug_print("[DEBUG] Make symlink:" + str(source) +  " -> " + str(link))
            os.symlink(source, link)
            if not FileHandler.__path_is_link:
                debug_print("[DEUG] Can't create symlink" + str(link))
                return False
            return True
        else:
            debug_print("[DEBUG] Symlink - source not exists: " + str(source))
            return False

    @staticmethod
    def chmod(path, value):
        if len(value) == 3 or len(value) == 4:
            value_oct = int(value, 8)
            try:
                debug_print("[DEBUG] Chmod " + str(path) + " with " + str(value))
                os.chmod(path, value_oct)
                debug_print("[DEBUG] Chmod " + str(path) + " with " + str(value) + " done")
                return True
            except:
                debug_print("[DEBUG] Chmod " + str(path) + " with " + str(value) + " failed")
                return False
        else:
            raise Exception("FileHandler.chmod value format error (755 or 0755): " + str(values))

    @staticmethod
    def get_path_permission(path):
        try:
            st = os.stat(path)
            oct_perm = oct(st.st_mode)
            output = oct_perm[-4:]
        except Exception as e:
            debug_print("Get file permissions {} filed: {}".format(path, e))
            output = None
        return output

    @staticmethod
    def get_path_ownership(path):
        from pwd import getpwuid
        from grp import getgrgid
        owner = getpwuid(os.stat(path).st_uid).pw_name
        group = getgrgid(os.stat(path).st_gid).gr_name
        return owner, group

    @staticmethod
    def rename(path, new_name):
        debug_print("[DEBUG] Rename file from " + path + " to " + new_name)
        os.rename(path, new_name)

    @staticmethod
    def remove(path, ignore=False):
        debug_print("[DEBUG] Remove " + path)
        try:
            exists, type_ = FileHandler.path_is_exists(path)
            if exists:
                if type_ == 'f':
                    os.remove(path)
                elif type_ == 'd':
                    shutil.rmtree(path)
        except Exception as e:
            if ignore:
                debug_print("[DEBUG] Removing " + path + " is forced to ignore failure: " + str(e))
            else:
                raise Exception("Cannot remove " + path + ": " + str(e))

    @staticmethod
    def extract_tar(targz, extract_path):
        debug_print("[DEUG] Extract file: " + targz + " to " + extract_path)
        tfile = tarfile.open(targz, 'r')
        tfile.extractall(extract_path)
        tfile.close()

    @staticmethod
    def extract_targz(targz, extract_path):
        debug_print("[DEBUG] Extract file: " + targz + " to " + extract_path)
        tfile = tarfile.open(targz, 'r:gz')
        tfile.extractall(extract_path)
        tfile.close()

    @staticmethod
    def copy(from_path, to_path):
        debug_print("[DEBUG] Copy " + from_path + " to " + to_path)
        try:
            shutil.copy(from_path, to_path)
            return True
        except Exception as e:
            debug_print("Copy error: {}".format(e))
            return False

    @staticmethod
    def move(from_path, to_path):
        #LogHandler.logger.debug("Move " + from_path + " to " + to_path)
        if FileHandler.__path_is_file(to_path):
            os.remove(to_path)
        shutil.move(from_path, to_path)

    @staticmethod
    def replace_infile_line_with_string(filename, search_string_in_lines, replace_string):
        if not os.path.exists(filename):
            raise Exception("replace_file_line_with_string(): File not found or accessable.")
        for line in fileinput.input(filename, inplace=True):
            if search_string_in_lines in line:
                debug_print(replace_string)
            else:
                debug_print(line)

    @staticmethod
    def insert_infile_line_before_string(filename, search_string_in_lines, insert_string):
        if not os.path.exists(filename):
            raise Exception("replace_file_line_with_string(): File not found or accessable.")
        done = False
        for line in fileinput.input(filename, inplace=True):
            if not done and search_string_in_lines in line:
                debug_print(insert_string + "\n" + line)
                done = True
            else:
                debug_print(line)

    @staticmethod
    def is_string_in_file(filename, substring):
        with open(filename) as fhandle:
            if substring in fhandle.read():
                return True
        return False


class SystemHandler:
    '''
    SystemHandler class contains disk, cpu, network
    related functionalities, like:
    * disk use
    * cpu usage
    * ifconfig
    * enivronmet variable handling
    * etc
    '''

    @staticmethod
    def signal_handler(signal, frame):
        '''
        SIGINT -> KeyBoardInterrupt
        # signal: 2
        # frame: <frame object at 0x1a84b78>
        '''
        debug_print("Execution was interrupted, Ctrl+C pressed:\nsignal: {}\nframe: {}".format(signal, frame))

    @staticmethod
    def python_info():
        python_version = sys.version
        exitcode, stdout, stderr = CommandHandler.run_command("debug_printenv | grep PYTHONPATH", shell=True)
        python_path = stdout.strip()
        debug_print("---------------")
        debug_print("PYTHON_VERSION: " + str(python_version))
        debug_print(python_path)
        debug_print("---------------")

    @staticmethod
    def ifconfig(regex=None):
        ifconfig_stdout = CommandHandler.run_command('ifconfig')[1].split('\n')
        result = {}
        new_entry_regex = re.compile(r'^(\w+)')
        ip4_address_regex = re.compile(r'^\s+inet addr:(?P<IP4>\d+\.\d+\.\d+\.\d+)\s*(Bcast:(?P<Bcast>\d+\.\d+\.\d+\.\d+))?\s*Mask:(?P<Mask>\d+\.\d+\.\d+\.\d+)')
        ip6_address_global_regex = re.compile(r'^\s+inet6 addr:\s*(.+?)\s+Scope:Global')
        op6_address_link_regex = re.compile(r'^\s+inet6 addr:\s*(.+?)\s+Scope:Link')
        empty_line_regex = re.compile(r'^\s*$')

        current_net = None
        for line in ifconfig_stdout:
            if(re.match(empty_line_regex, line)):
                current_net = None
                continue
            new_entry = re.match(new_entry_regex, line)
            if(new_entry):
                needed = True
                current_net = new_entry.group(1)
                if(regex is not None):
                    if(not re.match(regex, current_net)):
                        needed = False
                        current_net = None
                if needed:
                    result[current_net] = {}
                continue
            ip4 = re.match(ip4_address_regex, line)
            if(current_net is not None and ip4):
                result[current_net]['IP4_ADDRESS'] = ip4.group('IP4')
                result[current_net]['IP4_MASK'] = ip4.group('Mask')
                result[current_net]['IP4_BCAST'] = ip4.group('Bcast')
                continue
            ip6_global = re.match(ip6_address_global_regex, line)
            if(current_net is not None and ip6_global):
                result[current_net]['IP6_ADDRESS_GLOBAL'] = ip6_global.group(1)
                continue
            ip6_link = re.match(op6_address_link_regex, line)
            if(current_net is not None and ip6_link):
                result[current_net]['IP6_ADDRESS_LINK'] = ip6_link.group(1)
                continue
        return result

    @staticmethod
    def disk_usage(path="/"):
        '''
        [0] total GB
        [1] used GB
        [2] free GB
        '''
        st = os.statvfs(path)
        free = st.f_bavail * st.f_frsize
        total = st.f_blocks * st.f_frsize
        used = (st.f_blocks - st.f_bfree) * st.f_frsize
        # convert to Mb
        free = "{:.2f}".format((free / 1024 / 1024 / 1024))
        total = "{:.2f}".format((total / 1024 / 1024 / 1024))
        used = "{:.2f}".format((used / 1024 / 1024 / 1024))
        return total, used, free

    @staticmethod
    def ram_usage(limit_gb=None):
        '''
        [0] total GB
        [1] used GB
        [2] free GB
        [3] is_enough - in case of limit was provided
        '''
        is_enough = False
        cmd = "free -g"
        errorcode, stdout, stderr = CommandHandler.run_command(cmd, shell=True)
        if errorcode == 0:
            string_list = stdout.split()
            for index, word in enumerate(string_list):
                if "Mem" in word:
                    total = string_list[index +1]
                if "buffers/cache" in word:
                    used = string_list[index + 1]
                    free = string_list[index + 2]
                    break
        else:
            raise Exception("Command return with error: " + str(cmd))
        if limit_gb is not None and int(free) >= limit_gb:
            is_enough=True
        else:
            is_enough = None
        debug_print("[DEBUG] RAM: total: " + str(total) + " used: " + str(used) + " free: " + str(free) + " limit: " + str(limit_gb) + " state: " + str(is_enough))
        return total, used, free, is_enough

    @staticmethod
    def get_hostname():
        exitcode, stdout, stderr = CommandHandler.run_command('hostname')
        if exitcode == 0:
            return stdout.strip()
        else:
            return None

    @staticmethod
    def get_local_user():
        try:
            username = getpass.getuser()
        except Exception as e:
            debug_print("Get username failed: " + str(e))
            username = None
        return username

    @staticmethod
    def is_process_running(pid):
        path = "/proc/" + str(pid)
        if FileHandler.path_is_exists(path)[0]:
            debug_print("[DEBUG] {} is exists".format(pid))
            return True
        else:
            debug_print("[DEBUG] {} is not exists".format(pid))
            return False

    @staticmethod
    def env_var_is_exists(envvar, raise_exception=False):
        is_exists = False
        try:
            os.environ[envvar]
            is_exists = True
        except KeyError:
            if raise_exception:
                raise Exception("Environment variable: {} does not exists.".format(envvar))
        return is_exists

    @staticmethod
    def env_var_extend(env_var, value, separator=os.pathsep):
        try:
            os.environ[str(env_var)] += separator + value
        except:
            raise Exception("Cannot extend environment variable")

    @staticmethod
    def env_var_delete(env_var):
        try:
            if os.environ.get(env_var):
                debug_print("[DEBUG] Deleting env variable: " + env_var)
                del os.environ[env_var]
        except Exception as e:
            debug_print("[DEBUG] Cannot delete env var: " + env_var + " " + str(e))


class CommandHandler:
    '''
    CommandHandler class contains linux command execution
    related functionalities and evaluations
    '''

    @staticmethod
    def __run_command(command, forceshell=None, shell=False, debug=True):
        if forceshell is not None and type(forceshell) is str:
            if not shell: shell = True
            command = "{} -c '{}'".format(forceshell, command)
        # Command execution
        debug_print("[DEBUG] Execute command: " + str(command))
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
        _stdout = ""
        while True:
            output = proc.stdout.readline()
            if proc.poll() is not None and (output == b'' or output == ''):
                break
            if output:
                if debug:
                    print('\t[DEBUG] {}'.format(output.strip()))
                if isinstance(output, bytes):
                    try:
                        output = output.decode('utf-8')
                    except Exception as e:
                        # TODO ???? ROBUSTNESS FEATURE - COULD BE BUG!!!!
                        print("\n\n\n[WARNING] Cannot decode utf8 {}: {}\n\n\n".format(output, e))
                        output = ""
                _stdout += output
        _, _stderr = proc.communicate()
        _exitcode = proc.returncode
        return _exitcode, _stdout, _stderr

    @staticmethod
    def run_command(command, raise_exception=True, forceshell=None, shell=False, debug=True):
        '''
        * raise_exception: raise exception if execution raise or generate
          formal output with exitcode: 1
        * forceshell: add selected shell for execution:
            /bin/bash
            /bin/tcsh
        * shell: to invoke env var or shell specific functions set shell=True
        '''
        try:
            # Command execution
            exitcode, stdout, stderr = CommandHandler.__run_command(command, forceshell, shell, debug)
        except Exception as e:
            errmsg = "Command execution error" + str(e)
            if raise_exception:
                raise Exception(errmsg)
            else:
                debug_print(errmsg)
            # in case of raise_exception False - generate return values
            stdout = ""
            stderr = errmsg
            exitcode = 1
        # python3 return with bytes type - decode necessary
        if type(stdout) is bytes:
            stdout = stdout.decode()
        if type(stderr) is bytes:
            stderr = stderr.decode()
        return exitcode, stdout, stderr

    @staticmethod
    def run_command_stdout_list(command):
        exitcode, stdout, stderr = CommandHandler.run_command(command, raise_exception=True, forceshell=None, shell=True)
        stdout = stdout.split("\n").strip()
        return exitcode, stdout, stderr

    @staticmethod
    def run_command_wait_for_status_ok(command, forceshell=None, shell=False, retry=5, wait_sec=1, ok_exitcode=[0]):
        while retry > 0:
            exitcode, stdout, stderr = CommandHandler.run_command(command, forceshell, shell, raise_exception=False)
            if exitcode not in ok_exitcode:
                retry -= 1
                time.sleep(wait_sec)
            else:
                break
        if exitcode not in ok_exitcode:
            raise Exception("run_command_wait_for_status_ok timeout cmd: {}".format(command))
        return exitcode, stdout, stderr


if __name__ == "__main__":
    # Handle signals:
    signal.signal(signal.SIGINT, SystemHandler.signal_handler)
    time.sleep(2)

    exitcode, stdout, stderr = CommandHandler.run_command("ls")
    debug_print("exitcode: {}\nstdout: {}\nstderr: {}".format(exitcode, stdout, stderr))

    exitcode, stdout, stderr = CommandHandler.run_command("ls", forceshell="/bin/bash")
    debug_print("exitcode: {}\nstdout: {}\nstderr: {}".format(exitcode, stdout, stderr))

    debug_print(SystemHandler.ifconfig())

    SystemHandler.python_info()

    debug_print(SystemHandler.disk_usage())
    #debug_print(SystemHandler.ram_usage())
    debug_print(SystemHandler.get_hostname())
    debug_print(SystemHandler.get_local_user())

    testworkdir = SimplePopPushd()
    testworkdir.pushd('/')
    print(CommandHandler.run_command("ls"))
    testworkdir.popd()

