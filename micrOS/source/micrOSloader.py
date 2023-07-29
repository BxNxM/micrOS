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
try:
    from Debug import errlog_add
except Exception as e:
    print(f"Import error: {e}")
    errlog_add = None


def __is_micrOS():
    """
    Recovery mode for OTA update in case of connection/transfer failure
        .if_mode can have 2 possible values: webrepl or micros (strings)
    If the system is healthy / OTA update was successful
        .if_mode should contain: micros [return True]
    In other cases .if_mode should contain: webrepl [return False]

    It will force the system in bootup time to start
    webrepl (update) or micrOS (default)

    return
        True -> micrOS
        False -> webrepl
        * EOE (EndOfExecution) -> off
    """
    mode = 'micros'
    try:
        with open('.if_mode', 'r') as f:
            mode = f.read().strip().lower()
            if mode == 'micros':
                # start micrOS
                print("[loader][if_mode:True] .if_mode:micros -> micros interface")
                return True
    except Exception:
        # start micrOS
        print("[loader][if_mode:True] .if_mode file not exists -> micros interface")
        return True
    if mode == 'off':
        # micrOS OFF mode - USB connection / reboot improvement
        # RETURN TO MICROPYTHON - END OF EXECUTION !
        print("[loader][if_mode] .if_mode:off -> EOE, Bye!")
        from sys import exit
        exit(0)
    # start webrepl
    print("[loader][if_mode:False] .if_mode:webrepl -> webrepl interface")
    print("[loader][recovery mode] - manually selected in .if_mode file")
    return False


def __recovery_mode():
    # Recovery/Update mode (webrepl) - dependencies: Network, ConfigHandler
    from Network import auto_nw_config
    from ConfigHandler import cfgget
    pwd = cfgget('appwd')                       # Get pwd from config
    pwd = 'ADmin123' if pwd is None else pwd    # Default pwd if user pwd None
    # Set up network
    auto_nw_config()
    # Start webrepl
    try:
        import webrepl
        webrepl.start(password=pwd)
    except Exception as e:
        print(f"Webrepl import error: {e}")


def __auto_restart_event():
    """
    Poll .if_mode value main loop in case of webrepl (background) mode:
        Events for execute reboot:
            - value: webrepl    [wait for update -> updater writes webrepl value under update]
            - value: micros     [update was successful - reboot is necessary]
    :return:
    """
    from utime import sleep
    trigger_is_active = False
    wait_update_tout = 8
    # Wait after webrepl started for possible ota updates (~2*7= 14sec)
    while wait_update_tout > 0:
        # Wait for micros turns to webrepl until timeout
        if __is_micrOS():
            # micrOS mode
            print(f"[loader][ota auto-rebooter][micros][{wait_update_tout}] Wait for OTA update possible start")
            wait_update_tout -= 1
        else:
            print(f"[loader][ota auto-rebooter][webrepl/None][{wait_update_tout}] Update status: InProgress")
            # Set trigger  - if_mode changed to webrepl - ota update started - trigger wait
            trigger_is_active = True
        # Restart if trigger was activated
        if trigger_is_active and __is_micrOS():
            print("[loader][ota auto-rebooter][micros][trigger: True] OTA was finished - reboot")
            # Create cleanup indicator file for ConfigHandler
            with open('cleanup.pds', 'w') as f:
                f.write('')
            # Reboot machine
            from machine import reset
            reset()
        sleep(2)


def main():
    if __is_micrOS():
        # Main mode
        try:
            print("[loader][main mode] Start micrOS (default)")
            from micrOS import micrOS
            micrOS()
        except Exception as e:
            if traceback is not None: traceback.print_exc()
            # Handle micrOS system crash (never happened...but) -> webrepl mode default pwd: ADmin123
            print(f"[loader][main mode] micrOS start failed: {e}")
            print("[loader][main mode] -> [recovery mode]")
            if errlog_add is not None:
                errlog_add(f"[ERR][micrOSloader] micrOS start failed: {e}")
    # Recovery aka webrepl mode
    __recovery_mode()
    __auto_restart_event()


if __name__ == '__main__':
    main()
