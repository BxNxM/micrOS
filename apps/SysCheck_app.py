#!/usr/bin/env python3

import os
import sys
import time
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(MYPATH, '../tools'))
import socketClient

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
    info = "[ST] Run micrOS BgJob check [system clock &&1] + bgjob show / stop"
    print(info)

    # Start background thread loop
    cmd_list = ['system', 'clock', '&&1']
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
    cmd_list = ['bgjob', 'show']
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
    cmd_list = ['bgjob', 'show']
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
    return False, output + f' deltaT: {delta_cmd_rep_time} s'


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
               'reponse time': measure_package_response_time()
               }

    # Test Evaluation
    final_state = True
    ok_cnt = 0
    print("\n----------------------------------- micrOS System Test results -----------------------------------")
    print("\tTEST NAME\t\tSTATE\t\tDescription\n")
    for test, state_data in verdict.items():
        state = 'NOK'
        if state_data[0]:
            state = 'OK'
            ok_cnt += 1
        print(f"\t{test}:\t\t{state}\t\t[i]{state_data[1]}")
        final_state &= state_data[0]

    # Execution verdict
    print(f"\nPASS RATE: {round((ok_cnt/len(verdict.keys())*100), 1)} %")
    state = 'OK' if final_state else 'NOK'
    print(f"RESULT: {state}")
    print("--------------------------------------------------------------------------------------\n")


def execute(cmd_list):
    cmd_args = base_cmd() + cmd_list
    print("[ST] test cmd: {}".format(cmd_args))
    return socketClient.run(cmd_args)


if __name__ == "__main__":
    app()
