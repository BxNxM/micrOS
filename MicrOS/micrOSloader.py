"""
Module is responsible for invoke micrOS or recovery webrepl mode

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                    IMPORTS & START micrOS                     #
#################################################################


def __interface_mode():
    """
    Recovery mode for OTA update in case of connection/transfer failure
        .if_mode can have 2 possible values: webrepl or micros (strings)
    If the system is healhty / OTA update was successful
        .if_mode should contain: micros [return True]
    In other cases .if_mode should contain: webrepl [return False]

    It will force the system in bootup time to start
    webrepl (update) or micrOS (default)
    """

    try:
        with open('.if_mode', 'r') as f:
            if_mode = f.read().strip().lower()
    except Exception:
        # start micrOS
        return True

    if if_mode == 'micros':
        # start micrOS
        return True
    # start webrepl
    return False


def __recovery_mode():
    # Recovery mode (webrepl) - dependencies: Network, ConfigHandler
    from Network import auto_network_configuration
    from ConfigHandler import cfgget
    # Set up network
    auto_network_configuration()
    # Start webrepl
    import webrepl
    print(webrepl.start(password=cfgget('appwd')))


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
    wait_iteration_for_update_start = 3
    while wait_iteration_for_update_start >= 0:
        try:
            with open('.if_mode', 'r') as f:
                if_mode = f.read().strip().lower()
        except Exception:
            if_mode = None
        if if_mode is None or if_mode == 'webrepl':
            print("Check update status: InProgress")
        else:
            print("Wait for OTA update [{}]".format(wait_iteration_for_update_start))
            wait_iteration_for_update_start -= 1
        # Get trigger
        if if_mode is not None and if_mode == 'webrepl':
            trigger_is_active = True
        # Check value if trigger active
        if if_mode is not None and trigger_is_active and if_mode == 'micros':
            print("[micrOS updater - auto reboot after file upload]")
            import machine
            machine.reset()
        sleep(2)


def main():
    if __interface_mode():
        # Main mode
        from micrOS import micrOS
        try:
            micrOS()
        except Exception:
            __auto_restart_event()
    else:
        # Recovery mode
        __recovery_mode()
        __auto_restart_event()

if __name__ == '__main__':
    main()

