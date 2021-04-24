
def guimeta_fix_1_0_3_2():
    import ConfigHandler
    # Get full config dict
    full_conf_dict = ConfigHandler.cfgget()
    # Get guimeta value
    guimeta_value = full_conf_dict['guimeta']
    if guimeta_value.strip() != '...':
        # Change guimeta to enable new mode
        ConfigHandler.Data.CONFIG_CACHE['guimeta'] = '...'
        ConfigHandler.cfgput('guimeta', guimeta_value)
        return 'Modification was done :)'
    return 'Modification was already done :)'


#######################
# LM helper functions #
#######################

def help():
    return 'guimeta_fix_1_0_3_2', 'NOTE: Enable new method for guimeta value storage'
