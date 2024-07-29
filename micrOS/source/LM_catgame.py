from random import randint
from LM_servo import sduty, deinit, pinmap as pm
from utime import sleep_ms
from Types import resolve


def load():
    """
    Initialize catgame-servo module
    """
    return "catgame-servo module - loaded"


def game(repeat=10, delta=20):
    """
    Servo cat toy "mover" - left-right
    :param repeat int: repeat servo pos change
    :param delta int: center(75) +/-delta(35)
    :return str: verdict
    """
    sduty(75)
    for _ in range(0, repeat):
        sduty(randint(75-delta, 75+delta))
        sleep_ms(randint(20, 1500))
    sduty(75)
    return 'Game action'


def live_game(chance=10):
    """
    Generate game
    :param chance int: percent value 0-100
    :return str: verdict (action / no action)
    """
    action = randint(1, 10)
    if action <= int(chance/10):
        return game(repeat=5)
    return 'No action'


def stop():
    """
    Stop game - home position (75) + deinit
    :return str: servo verdict
    """
    out = sduty(75)
    deinit()
    return out


#######################
# LM helper functions #
#######################

def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    return pm()


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('BUTTON game repeat=10',
                             'SLIDER live_game chance=<10-90>',
                             'BUTTON stop', 'pinmap',
                             'load'), widgets=widgets)
