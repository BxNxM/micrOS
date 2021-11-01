#########################################
#       ANALOG rgb CONTROLLER PARAMS    #
#########################################
from sys import platform
from utime import sleep_ms
from Common import transition
from ConfigHandler import cfgget


class Data:
    CWWW_OBJS = (None, None)
    CWWW_CACHE = [600, 600, 0]           # cold white / warm white / state
    PERSISTENT_CACHE = False
    FADE_OBJS = (None, None)


#########################################
#      ANALOG rgb WITH 3 channel PWM    #
#########################################

def __cwww_init():
    if Data.CWWW_OBJS[0] is None or Data.CWWW_OBJS[1] is None:
        from machine import Pin, PWM
        from LogicalPins import physical_pin
        cw = Pin(physical_pin('cwhite'))
        ww = Pin(physical_pin('wwhite'))
        if platform == 'esp8266':
            Data.CWWW_OBJS = (PWM(cw, freq=1024),
                              PWM(ww, freq=1024))
        else:
            Data.CWWW_OBJS = (PWM(cw, freq=20480),
                              PWM(ww, freq=20480))
    return Data.CWWW_OBJS


def __persistent_cache_manager(mode):
    """
    pds - persistent data structure
    modes:
        r - recover, s - save
    """
    if not Data.PERSISTENT_CACHE:
        return
    if mode == 's':
        # SAVE CACHE
        with open('cwww.pds', 'w') as f:
            f.write(','.join([str(k) for k in Data.CWWW_CACHE]))
        return
    try:
        # RESTORE CACHE
        with open('cwww.pds', 'r') as f:
            Data.CWWW_CACHE = [int(data) for data in f.read().strip().split(',')]
    except:
        pass


def load_n_init(cache=None):
    """
    Initiate Cold white / Warm white LED module
    - Load .pds file for that module
    - restore state machine from .pds
    :param cache: file state machine chache: True(default)/False
    :return: Cache state
    """
    from sys import platform
    if cache is None:
        Data.PERSISTENT_CACHE = True if platform == 'esp32' else False
    else:
        Data.PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')        # recover data cache
    if Data.CWWW_CACHE[2] == 1:
        toggle(True)                       # Recover state if ON
    else:
        white(0, 0, smooth=False)          # Init pins at bootup
    return "CACHE: {}".format(Data.PERSISTENT_CACHE)


def white(c=None, w=None, smooth=True, force=True):
    """
    Set RGB values with PWM signal
    :param c: cold white value   0-1000
    :param w: warm white value 0-1000
    :param smooth: runs white channels change with smooth effect
    :param force: clean fade generators and set color
    :return: verdict string
    """
    def __buttery(ww_from, cw_from, ww_to, cw_to):
        step_ms = 2
        interval_sec = 0.3
        if Data.CWWW_CACHE[2] == 0:
            # Turn from OFF to on (to whites)
            ww_from, cw_from = 0, 0
            Data.CWWW_CACHE[2] = 1
        ww_gen = transition(from_val=ww_from, to_val=ww_to, step_ms=step_ms, interval_sec=interval_sec)
        cw_gen = transition(from_val=cw_from, to_val=cw_to, step_ms=step_ms, interval_sec=interval_sec)
        for _ww in ww_gen:
            Data.CWWW_OBJS[1].duty(_ww)
            Data.CWWW_OBJS[0].duty(cw_gen.__next__())
            sleep_ms(step_ms)

    __cwww_init()
    if force and Data.FADE_OBJS[0]:
        Data.FADE_OBJS = (None, None)
    c = Data.CWWW_CACHE[0] if c is None else c
    w = Data.CWWW_CACHE[1] if w is None else w
    if smooth:
        __buttery(ww_from=Data.CWWW_CACHE[1], cw_from=Data.CWWW_CACHE[0], ww_to=w, cw_to=c)
    else:
        Data.CWWW_OBJS[0].duty(c)
        Data.CWWW_OBJS[1].duty(w)
    # Cache channel duties if ON
    if c > 0 or w > 0:
        Data.CWWW_CACHE = [Data.CWWW_OBJS[0].duty(), Data.CWWW_OBJS[1].duty(), 1]
    else:
        Data.CWWW_CACHE[2] = 0
    # Save config
    __persistent_cache_manager('s')
    return "SET : CW{} WW{}".format(c, w)


def toggle(state=None, smooth=True):
    """
    Toggle led state based on the stored state
    :param state: True(1)/False(0)
    :param smooth: runs white channels change with smooth effect
    :return: verdict
    """
    if state is not None:
        Data.CWWW_CACHE[2] = 0 if state else 1
    if Data.CWWW_CACHE[2]:
        white(0, 0, smooth=smooth, force=False)
        return "OFF"
    # Turn ON with smooth "hack"
    if smooth:
        cw, ww = Data.CWWW_CACHE[0], Data.CWWW_CACHE[1]
        Data.CWWW_CACHE[0], Data.CWWW_CACHE[1] = 0, 0
        white(cw, ww, force=False)
        return "ON"
    # Turn ON without smooth
    white(force=False)
    return "ON"


def set_transition(cw, ww, sec):
    """
    Set transition white channel change for long dimming periods < 30sec
    - creates the 2 white dimming generators
    :param cw: cold white value   0-1000
    :param ww: warm white value 0-1000
    :param sec: transition length in sec
    :return: info msg string
    """
    Data.CWWW_CACHE[2] = 1
    timirqseq = cfgget('timirqseq')
    from_cw = Data.CWWW_CACHE[0]
    from_ww = Data.CWWW_CACHE[1]
    # Generate cold white + warm white transition object (generator)
    Data.FADE_OBJS = (transition(from_val=from_cw, to_val=cw, step_ms=timirqseq, interval_sec=sec),
                      transition(from_val=from_ww, to_val=ww, step_ms=timirqseq, interval_sec=sec))
    return 'Settings was applied... wait for: run_transition'


def run_transition():
    """
    Transition execution - white channels change for long dimming periods
    - runs the generated 2 white dimming generators
    :return: Execution verdict
    """
    if None not in Data.FADE_OBJS:
        try:
            cw = Data.FADE_OBJS[0].__next__()
            ww = Data.FADE_OBJS[1].__next__()
            if Data.CWWW_CACHE[2] == 1:
                white(int(cw), int(ww), smooth=False, force=False)
                return "SET : CW{} WW{}".format(cw, ww)
            return 'Run deactivated'
        except:
            Data.FADE_OBJS = (None, None)
            return 'GenEnd.'
    return 'Nothing to run.'


#######################
# LM helper functions #
#######################
def status(lmf=None):
    # Cold White / Warm White dedicated widget input - [OK]
    return {'CW': Data.CWWW_CACHE[0], 'WW': Data.CWWW_CACHE[1], 'S': Data.CWWW_CACHE[2]}


def help():
    return 'white c=<0-1000> w=<0-1000> smooth=True force=True',\
           'toggle state=None smooth=True', 'load_n_init', \
           'set_transition cw=<0-1000> ww=<0-1000> sec', 'run_transition', 'status'
