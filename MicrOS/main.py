"""
Module is responsible for import and execute micrOS IoT FW

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                    IMPORTS & START micrOS                     #
#################################################################


def interface_mode():
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


def recovery_mode():
    # Recovery mode (webrepl) - dependencies: Network, ConfigHandler
    from Network import auto_network_configuration
    from ConfigHandler import cfgget
    # Set up network
    auto_network_configuration()
    # Start webrepl
    import webrepl
    print(webrepl.start(password=cfgget('appwd')))


if interface_mode():
    # Main mode
    from micrOS import micrOS
    micrOS()
else:
    # Recovery mode
    recovery_mode()
