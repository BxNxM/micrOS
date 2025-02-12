"""
Source: https://how2electronics.com/temt6000-ambient-light-sensor-arduino-measure-light-intensity/
ADC.ATTN_0DB — the full range voltage: 1.2V
ADC.ATTN_2_5DB — the full range voltage: 1.5V
ADC.ATTN_6DB — the full range voltage: 2.0V
ADC.ATTN_11DB — the full range voltage: 3.3V
"""
from Common import SmartADC, micro_task
from Types import resolve
try:
    import LM_intercon as InterCon
except:
    InterCon = None
from microIO import bind_pin, pinmap_search


ADC = None


def __init_tempt6000():
    """
    Setup ADC
    """
    global ADC
    if ADC is None:
        ADC = SmartADC(bind_pin('temp6000'))
    return ADC


def load():
    """
    Initialize TEMPT6000 light sensor module
    """
    __init_tempt6000()
    return "TEMPT6000 light sensor module - loaded"


def intensity():
    """
    Measure light intensity in %
    - result is 20 result average (noise reduction)
    """
    percent = 0
    adc = __init_tempt6000()
    for _ in range(20):
        percent += adc.get()['percent']
    percent = round(percent/20, 1)
    return {'light intensity [%]': percent}


def illuminance():
    """
    Measure light illuminance in flux
    - result is 20 result average (noise reduction)
    """
    volts = 0
    adc = __init_tempt6000()
    for _ in range(20):
        volts += adc.get()['volt']
    volts = round(volts/20, 1)
    amps = volts / 10000.0                    # across 10,000 Ohms (voltage divider circuit)
    microamps = amps * 1000000
    lux = '{:.2f}'.format(microamps * 2.0)
    return {'illuminance [lux]': lux}


async def _task(on, off, threshold, tolerance=2, check_ms=5000):
    last_ev = ""
    on = on.split()
    off = off.split()
    check_ms = 5000 if check_ms < 5000 else check_ms        # MIN 5s check period
    with micro_task(tag="light_sensor.intercon") as my_task:
        my_task.out = f"threshold: {threshold} - starting"
        while True:
            percent = int(tuple(intensity().values())[0])
            # TURN ON
            if percent <= threshold:
                if on != last_ev:
                    if InterCon is not None:
                        host = on[0]
                        cmd = ' '.join(on[1:])
                        InterCon.send_cmd(host, cmd)
                    my_task.out = f"{percent}% <= threshold: {threshold}% - ON"
                    last_ev = on
            elif percent > threshold+tolerance:     # +tolerance to avoid "on/off/on/off" on threshold limit
                if off != last_ev:
                    if InterCon is not None:
                        host = off[0]
                        cmd = ' '.join(off[1:])
                        InterCon.send_cmd(host, cmd)
                    my_task.out = f"{percent}% > threshold: {threshold+tolerance}% - OFF"
                    last_ev = off
            await my_task.feed(sleep_ms=check_ms)   # Sample every <check_ms> sec


def subscribe_intercon(on, off, threshold=4, tolerance=2, sample_sec=60):
    """
    [TASK] ON/OFF command sender over intercon on given threshold
    :param on: on callback to send: "host cmd"
    :param off: off callback to send: "host cmd"
    :param threshold: percentage value for on(under) /off(above)
    :param tolerance: off tolerance value -> off event: threshold+tolerance
    :param sample_sec: light measure task period in sec (also means event frequency)
    """
    # Start play - servo XY in async task
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    state = micro_task(tag="light_sensor.intercon", task=_task(on, off, threshold, tolerance=tolerance,
                                                               check_ms=sample_sec*1000))
    if state:
        return 'Light sensor remote trigger starts'
    return 'Light sensor remote trigger - already running'


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
    return pinmap_search('temp6000')


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('TEXTBOX intensity', 'TEXTBOX illuminance',
                             'subscribe_intercon on off threshold=1 tolerance=2 sample_sec=60',
                             'pinmap', 'load', '[Info] sensor:TEMP600'), widgets=widgets)

