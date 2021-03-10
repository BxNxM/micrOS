
def guimeta_fix_0_10_3_0():
    import ConfigHandler
    # Get full config dict
    full_conf_dict = ConfigHandler.read_cfg_file()
    # Get guimeta value
    guimeta_value = full_conf_dict['guimeta']
    if guimeta_value.strip() != '...':
        # Save guimeta value to file
        ConfigHandler.__disk_keys('guimeta', guimeta_value)
        # Change guimeta to enable new mode
        full_conf_dict['guimeta'] = '...'
        # Save modified dict to file
        ConfigHandler.__write_cfg_file(full_conf_dict)
        return 'Modification was done :)'
    return 'Modification was already done :)'


def help():
    return 'guimeta_fix_0_10_3_0', 'NOTE: Enable new method for guimeta value storage'
