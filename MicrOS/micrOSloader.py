"""
Module is responsible for invoke micrOS or recovery webrepl mode

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                    IMPORTS & START micrOS                     #
#################################################################
try:
    # Simulator debug requirement...
    import traceback
except:
    traceback = None


def __interface_mode():
    """
    Recovery mode for OTA update in case of connection/transfer failure
        .if_mode can have 2 possible values: webrepl or micros (strings)
    If the system is healhty / OTA update was successful
        .if_mode should contain: micros [return True]
    In other cases .if_mode should contain: webrepl [return False]

    It will force the system in bootup time to start
    webrepl (update) or micrOS (default)

    return
        True -> micrOS
        False -> webrepl
    """

    try:
        with open('.if_mode', 'r') as f:
            if_mode = f.read().strip().lower()
    except Exception:
        # start micrOS
        print("[loader][if_mode:True] .if_mode file not exists -> micros interface")
        return True

    if if_mode == 'micros':
        # start micrOS
        print("[loader][if_mode:True] .if_mode:{} -> micros interface".format(if_mode))
        return True
    # start webrepl
    print("[loader][if_mode:False] .if_mode:{} -> webrepl interface".format(if_mode))
    return False


def __recovery_mode():
    # Recovery mode (webrepl) - dependencies: Network, ConfigHandler
    from Network import auto_network_configuration
    try:
        from ConfigHandler import cfgget
    except:
        cfgget = None
    # Set up network
    auto_network_configuration()
    # Start webrepl
    import webrepl
    appwd = 'ADmin123' if cfgget is None else cfgget('appwd')
    print(webrepl.start(password=appwd))


def __auto_restart_event():
    """
    Poll .if_mode value main loop in case of webrepl (background) mode:
        Events for execute reboot:
            - value: webrepl    [wait for update -> updater writes webrepl value under update]
            - value: micros     [update was successful - reboot is necessary]
    :return:
    """
    from time import sleep
    trigger_is_active = False
    wait_iteration_for_update_start = 5
    # Wait after webrepl started for possible ota updates (~10 sec)
    while wait_iteration_for_update_start >= 0:
        # Parse .if_mode - interface selector
        try:
            with open('.if_mode', 'r') as f:
                if_mode = f.read().strip().lower()
        except Exception:
            if_mode = None
        if if_mode is None or if_mode == 'webrepl':
            print("[loader][ota auto-rebooter][webrepl/None][{}] Update status: InProgress".format(wait_iteration_for_update_start))
        else:
            print("[loader][ota auto-rebooter][micros][{}] Wait for OTA update possible start".format(wait_iteration_for_update_start))
            wait_iteration_for_update_start -= 1
        # Get trigger  - if_mode changed to webrepl - ota update started - trigger wait
        if not trigger_is_active and if_mode is not None and if_mode == 'webrepl':
            trigger_is_active = True
            print("\t[loader][ota auto-rebooter] Trigger activated for wait ota finish")
        # Check value if trigger active
        if if_mode is not None and trigger_is_active and if_mode == 'micros':
            print("[loader][ota auto-rebooter][micros][trigger: True] OTA was finished - reboot")
            import machine
            machine.reset()
        sleep(2)


def main():
    if __interface_mode():
        # Main mode
        try:
            print("[loader][main mode] Start micrOS (default)")
            from micrOS import micrOS
            micrOS()
        except Exception as e:
            if traceback is not None: traceback.print_exc()
            # Handle micrOS system crash (never happened...but) -> webrepl mode default pwd: ADmin123
            print("[loader][main mode] micrOS start failed: {}".format(e))
            print("[loader][main mode] -> [recovery mode]")
            __recovery_mode()
            __auto_restart_event()
    else:
        # Recovery mode
        print("[loader][recovery mode] - manually selected in .if_mode file")
        __recovery_mode()
        __auto_restart_event()


if __name__ == '__main__':
    main()

