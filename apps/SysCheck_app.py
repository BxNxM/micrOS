#!/usr/bin/env python3

import os
import sys
import time
import socket
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../tools'))
import socketClient
sys.path.append(os.path.join(MYPATH, '../tools/MicrOSDevEnv'))
from TerminalColors import Colors

# FILL OUT
DEVICE = '__simulator__'


def base_cmd():
    return ['--dev', DEVICE]


def single_cmd_exec_check():
    info = "[ST] Run single command execution check [hello]"
    print(info)
    cmd_list = ['hello']
    output = execute(cmd_list)
    if output[0]:
        if output[1].startswith("hello:"):
            return True, info
    return False, info


def lm_cmd_exec_check():
    info = "[ST] Run Load Module command execution check [system heartbeat]"
    print(info)
    cmd_list = ['system heartbeat']
    output = execute(cmd_list)
    if output[0]:
        if output[1].strip() == '<3 heartbeat <3':
            return True, info
    return False, info


def micrOS_config_get():
    info = "[ST] Run micrOS config get [conf -> socport]"
    print(info)
    cmd_list = ['config', '<a>', 'socport']
    output = execute(cmd_list)
    if output[0]:
        if output[1].strip() == '9008':
            return True, info
    return False, info


def micrOS_config_set():
    info = "[ST] Run micrOS config set [conf -> gmttime]"
    gmttime_bak = None
    print(info)

    # [1] Get actual gmttime value
    cmd_list = ['config', '<a>', 'gmttime']
    output = execute(cmd_list)
    if output[0]:
        try:
            gmttime_bak = int(output[1].strip())
        except:
            return False, f"{info} + get gmttime error: {output[1]}"

    # [2] Set x+1 value as expected
    gmttime_expected = gmttime_bak+1
    cmd_list = ['config', '<a>', 'gmttime', str(gmttime_expected)]
    output = execute(cmd_list)
    if output[0]:
        if output[1].strip() != 'Saved':
            return False, f"{info} + gmttime overwrite issue: {output[1]}"

    # [3] Get modified gmttime value - veridy [2] step
    cmd_list = ['config', '<a>', 'gmttime']
    output = execute(cmd_list)
    if output[0]:
        if int(output[1].strip()) != gmttime_expected:
            return False, f"{info} + gmttime modified value error: {output[1]} != {gmttime_expected}"

    # Restore original value
    cmd_list = ['config', '<a>', 'gmttime', str(gmttime_bak)]
    output = execute(cmd_list)
    if output[0]:
        if output[1].strip() != 'Saved':
            return False, f"{info} + gmttime overwrite issue: {output[1]}"

    # Final verdict
    return True, info


def micrOS_bgjob_one_shot_check():
    info = "[ST] Run micrOS BgJob check [system clock &]"
    print(info)

    for _ in range(0, 2):
        cmd_list = ['system', 'clock', '&']
        output = execute(cmd_list)
        if output[0]:
            if 'Start system.clock' not in output[1].strip():
                return False, f'{info} + not expected return: {output[1]}'
    return True, info


def micrOS_bgjob_loop_check():
    info = "[ST] Run micrOS BgJob check [system clock &&] + bgjob show / stop"
    print(info)

    # Start background thread loop
    cmd_list = ['system', 'clock', '&&']
    output = execute(cmd_list)
    if output[0]:
        if 'Start system.clock' not in output[1].strip():
            return False, f'[Start Bg. Loop] {info} + not expected return: {output[1]}'

    # Attempt to overload background thread
    cmd_list = ['system', 'clock', '&&']
    output = execute(cmd_list)
    if output[0]:
        if 'system.clock is Busy' not in output[1].strip():
            return False, f'[Overload thread] {info} + not expected return: {output[1]}'

    # Show BgJob status - running
    cmd_list = ['bgjob', 'show', '>json']
    output = execute(cmd_list)
    if output[0]:
        if "'isbusy': True" not in output[1].strip():
            return False, f'[Thread running] {info} + not expected return: {output[1]}'

    # Stop BgJob
    cmd_list = ['bgjob', 'stop']
    output = execute(cmd_list)
    if output[0]:
        if 'Stop' not in output[1].strip() or 'system.clock' not in output[1].strip():
            return False, f'[Stop thread] {info} + not expected return: {output[1]}'

    # Show BgJob status - stopped
    cmd_list = ['bgjob', 'show', '>json']
    for _ in range(0, 5):
        output = execute(cmd_list)
        if output[0]:
            if "'isbusy': False" in output[1].strip():
                # Return test verdict
                return True, info

    # Failed verdict
    return False, f'[Thread not stopped]{info} + not expected return: {output[1]}'


def micrOS_get_version():
    info = "[ST] Run micrOS get version [version]"
    print(info)
    cmd_list = ['version']
    output = execute(cmd_list)
    if output[0]:
        if '.' in output[1].strip() and '-' in output[1].strip():
            return True, f"{info} v:{output[1].strip()}"
    return False, info


def json_format_check():
    info = "[ST] Run micrOS raw output check aka >json [system rssi >json]"
    print(info)
    cmd_list = ['system rssi >json']
    output = execute(cmd_list)
    if output[0] and output[1].startswith("{") and output[1].endswith("}"):
        return True, info + f" out: {output[1]}"
    return False, info + f" out: {output[1]}"


def negative_interface_check():
    info = "[ST] Run micrOS Negative API check [Invalid CMDs + conf]"
    print(info)

    cmd_list = ['Apple']
    output = execute(cmd_list)
    if output[0]:
        if 'SHELL: type help for single word commands' not in output[1].strip():
            return False, f'[Wrong single command] {info} + not expected return: {output[1]}'

    cmd_list = ['Apple', 'test']
    output = execute(cmd_list)
    if output[0]:
        if 'no module named' not in output[1].strip().lower():
            return False, f'[Missing module] {info} + not expected return: {output[1]}'

    cmd_list = ['conf', '<a>',  'gmttimaaaa']
    output = execute(cmd_list)
    if output[0]:
        if output[1].strip() != 'None':
            return False, f'[Config invalid key] {info} + not expected return: {output[1]}'

    cmd_list = ['conf', '<a>', 'gmttime', '"type"']
    output = execute(cmd_list)
    if output[0]:
        if output[1].strip() != 'Failed to save':
            return False, f'[Config invalid key type] {info} + not expected return: {output[1]}'

    return True, info


def measure_package_response_time():
    info = "[ST] Measure response time [system heartbeat]x10"
    print(info)
    cmd_list = ['system heartbeat', '<a>',
                'system heartbeat', '<a>',
                'system heartbeat', '<a>',
                'system heartbeat', '<a>',
                'system heartbeat', '<a>',
                'system heartbeat', '<a>',
                'system heartbeat', '<a>',
                'system heartbeat', '<a>',
                'system heartbeat', '<a>',
                'system heartbeat']
    # Start time
    start = time.time()
    # Command exec
    output = execute(cmd_list)
    # Stop time
    end = time.time() - start
    # Get average response time
    delta_cmd_rep_time = round(end/10, 1)
    # Create verdict
    print(output)
    if output[0] and output[1] == '<3 heartbeat <3':
        return True, info + f' deltaT: {delta_cmd_rep_time} s'
    return False, info + f' {output[0]}:{output[1]} deltaT: {delta_cmd_rep_time} s'


def micros_alarm_check():
    info = "[ST] Test alarm state - system alarms should be null"
    print(info)
    cmd_list = ['system alarms']
    output = execute(cmd_list)
    alarm_cnt = 0
    if output[0]:
        try:
            alarm_cnt = output[1].split(':')[-1]
            alarm_cnt = int(alarm_cnt.strip())
        except Exception as e:
            alarm_cnt = 404
            print(e)
        if alarm_cnt > 0:
            return True, info + f" -1 !!!WARN!!! [{alarm_cnt}] out: {output[1]}"
    return True, info + f" [{alarm_cnt}] out: {output[1]}"


def oled_msg_end_result(result):
    cmd_list = ['system module >json']
    output = execute(cmd_list)
    if output[0] and 'LM_oled_ui' in output[1]:
        cmd_list = [f'oled_ui msgbox "{result} %"']
        print(execute(cmd_list))


def check_device_by_hostname(dev):
    devlocal = '{}.local'.format(dev)
    info_msg = '[ST] Check host {} and resolve IP'.format(devlocal)
    print(info_msg)
    try:
        ip = socket.gethostbyname(devlocal)
    except Exception as e:
        ip = None
        return False, '{}: {} error: {}'.format(info_msg, ip, e)
    if '.' in ip:
        return True, '{}: {}'.format(info_msg, ip)
    return False, '{}: {}'.format(info_msg, ip)


def check_robustness_exception():
    info_msg = '[ST] Check robustness - exception [robustness raise_error]'
    print(info_msg)
    cmd_list = ['robustness raise_error']
    output = execute(cmd_list)
    if output[0] and "exec_lm_core LM_robustness->raise_error: Test exception" in output[1]:
        return True, f'{info_msg}: Valid error msg: exec_lm_core *->raise_error: *'
    else:
        return False, f'{info_msg}: {output}'


def check_robustness_memory():
    info_msg = '[ST] Check robustness - memory_leak [robustness memory_leak 20]'
    print(info_msg)
    cmd_list = ['robustness memory_leak 20']
    output = execute(cmd_list)
    if output[0] and "[20] RAM Alloc" in output[1]:
        end_result = output[1].split("\n")[-1]
        return True, f'{info_msg}: Mem alloc: {end_result}'
    else:
        return False, f'{info_msg}: {output}'


def check_robustness_recursion():
    info_msg = '[ST] Check robustness - recursion [robustness recursion_limit 5]'
    print(info_msg)
    cmd_list = ['robustness recursion_limit 5']
    output = execute(cmd_list)
    if output[0] and "0" in output[1].split("\n")[-1]:
        return True, f'{info_msg}'
    else:
        return False, f'{info_msg}: {output}'


def app(devfid=None):
    global DEVICE
    if devfid is not None:
        DEVICE = devfid

    # Get test verdict
    verdict = {'single_cmds': single_cmd_exec_check(),
               'lm_cmd_exec': lm_cmd_exec_check(),
               'config_get': micrOS_config_get(),
               'config_set': micrOS_config_set(),
               'thread_oneshot': micrOS_bgjob_one_shot_check(),
               'thread_loop': micrOS_bgjob_loop_check(),
               'version': micrOS_get_version(),
               'json_check': json_format_check(),
               'reponse time': measure_package_response_time(),
               'negative_api': negative_interface_check(),
               'dhcp_hostname': check_device_by_hostname(DEVICE),
               'lm_exception': check_robustness_exception(),
               'mem_alloc': check_robustness_memory(),
               'recursion': check_robustness_recursion(),
               'micros_alarms': micros_alarm_check()
               }

    # Test Evaluation
    final_state = True
    ok_cnt = 0
    print(f"\n----------------------------------- micrOS System Test results on {DEVICE} device -----------------------------------")
    print("\tTEST NAME\t\tSTATE\t\tDescription\n")
    for test, state_data in verdict.items():
        state = Colors.ERR + 'NOK' + Colors.NC
        if state_data[0]:
            state = Colors.OK + 'OK' + Colors.NC
            ok_cnt += 1
        print(f"\t{test}:\t\t{state}\t\t[i]{state_data[1]}")
        final_state &= state_data[0]

    # Execution verdict
    pass_rate = round((ok_cnt/len(verdict.keys())*100), 1)
    print(f"\nPASS RATE: {pass_rate} %")
    state = 'OK' if final_state else 'NOK'
    colorful_state = Colors.OK + state + Colors.NC if state == 'OK' else Colors.WARN + state + Colors.NC
    print(f"RESULT: {colorful_state}")
    print("--------------------------------------------------------------------------------------\n")
    oled_msg_end_result(f"System[{state}] {pass_rate}")


def execute(cmd_list):
    cmd_args = base_cmd() + cmd_list
    print("[ST] test cmd: {}".format(cmd_args))
    return socketClient.run(cmd_args)


if __name__ == "__main__":
    app()
