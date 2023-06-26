from sys import platform
from utime import sleep
from LogicalPins import physical_pin, pinmap_dump
from Common import micro_task
import uasyncio as asyncio


#########################################
#      BUZZER PWM CONTROLLER PARAMS     #
#########################################
__BUZZER_OBJ = None
# DATA: state:ON/OFF, freq:0-1000
__BUZZER_CACHE = [600]
__PERSISTENT_CACHE = False
__TASK_TAG = "buzzer._play"

#########################################
#              BUZZER RTTL              #
#########################################

NOTE = [
    440.0,  # A
    493.9,  # B or H
    261.6,  # C
    293.7,  # D
    329.6,  # E
    349.2,  # F
    392.0,  # G
    0.0,    # pad

    466.2,  # A#
    0.0,
    277.2,  # C#
    311.1,  # D#
    0.0,
    370.0,  # F#
    415.3,  # G#
    0.0,
]


# Ring Tone Transfer Language
class RTTTL:

    def __init__(self, tune):
        self.msec_per_whole_note = 0.0
        self.default_octave = None
        self.default_duration = None
        self.bpm = None
        self.tune_idx = 0
        rtttl_fregs = tune.split(':')
        if len(rtttl_fregs) < 2:
            raise ValueError('RTTTL input structure error. [title:defaults:song]')
        if len(rtttl_fregs) == 3:
            # Regular form
            self.tune = rtttl_fregs[2]
            self.parse_defaults(rtttl_fregs[1])
        else:
            # No title form
            if '=' in rtttl_fregs[0]:
                self.tune = rtttl_fregs[1]
                self.parse_defaults(rtttl_fregs[0])
            else:
                raise ValueError('RTTTL input structure error. [defaults:song]')

    def parse_defaults(self, defaults):
        # Example: d=4,o=5,b=140
        defaults = {str(idval.split('=')[0]).strip(): int(idval.split('=')[1]) for idval in defaults.split(',')}
        self.default_octave = defaults['o']
        self.default_duration = defaults['d']
        self.bpm = defaults['b']
        # 240000 = 60 sec/min * 4 beats/whole-note * 1000 msec/sec
        self.msec_per_whole_note = 240000.0 / self.bpm

    def next_char(self):
        if self.tune_idx < len(self.tune):
            char = self.tune[self.tune_idx]
            self.tune_idx += 1
            if char == ',':
                char = ' '
            return char
        return '|'

    def notes(self):
        """Generator which generates notes. Each note is a tuple where the
           first element is the frequency (in Hz) and the second element is
           the duration (in milliseconds).
        """
        while True:
            # Skip blank characters and commas
            char = self.next_char()
            while char == ' ':
                char = self.next_char()

            # Parse duration, if present. A duration of 1 means a whole note.
            # A duration of 8 means 1/8 note.
            duration = 0
            while char.isdigit():
                duration *= 10
                duration += ord(char) - ord('0')
                char = self.next_char()
            if duration == 0:
                duration = self.default_duration

            if char == '|':     # marker for end of tune
                return

            note = char.lower()
            if 'a' <= note <= 'g':
                note_idx = ord(note) - ord('a')
            elif note == 'h':
                note_idx = 1    # H is equivalent to B
            else:
                note_idx = 7    # pause
            char = self.next_char()

            # Check for sharp note
            if char == '#':
                note_idx += 8
                char = self.next_char()

            # Check for duration modifier before octave
            # The spec has the dot after the octave, but some places do it
            # the other way around.
            duration_multiplier = 1.0
            if char == '.':
                duration_multiplier = 1.5
                char = self.next_char()

            # Check for octave
            if '4' <= char <= '7':
                octave = ord(char) - ord('0')
                char = self.next_char()
            else:
                octave = self.default_octave

            freq = NOTE[note_idx] * (1 << (octave - 4))
            msec = (self.msec_per_whole_note / duration) * duration_multiplier

            yield freq, msec

#########################################
#         BUZZER MAIN FUNCTIONS         #
#########################################


def __buzzer_init():
    global __BUZZER_OBJ
    if __BUZZER_OBJ is None:
        from machine import Pin, PWM
        dimmer_pin = Pin(physical_pin('buzzer'))
        if platform == 'esp8266':
            __BUZZER_OBJ = PWM(dimmer_pin, freq=600)
        else:
            __BUZZER_OBJ = PWM(dimmer_pin, freq=600)
        __BUZZER_OBJ.duty(512)      # 50%
    return __BUZZER_OBJ


def __persistent_cache_manager(mode='r'):
    """
    pds - persistent data structure
    modes:
        r - recover, s - save
    """
    if not __PERSISTENT_CACHE:
        return
    global __BUZZER_CACHE
    if mode == 's':
        # SAVE CACHE
        with open('buzzer.pds', 'w') as f:
            f.write(','.join([str(k) for k in __BUZZER_CACHE]))
        return
    try:
        # RESTORE CACHE
        with open('buzzer.pds', 'r') as f:
            __BUZZER_CACHE = [int(data) for data in f.read().strip().split(',')]
    except:
        pass


def __play_tone(freq, msec):
    buzz = __buzzer_init()
    if freq > 0:
        buzz.freq(int(freq))    # Set frequency
        buzz.duty(512)          # 50% duty cycle
    sleep(msec*0.001)           # Play for a number of msec
    buzz.duty(0)                # Stop playing


#########################
# Application functions #
#########################

def bipp(repeat=1, freq=None):
    """
    Buzzer bipp sound generator
    :param repeat int: bipp count
    :param freq int: 0-1000 default: 600
    :return str: Verdict string
    """
    global __BUZZER_CACHE
    # restore data from cache if it was not provided
    freq = int(__BUZZER_CACHE[0] if freq is None else freq)
    for _ in range(repeat):
        __play_tone(freq, 150)    # Play bip tone
        sleep(0.1)
    __BUZZER_CACHE[0] = freq
    __persistent_cache_manager('s')
    return "Bi{} on {} Hz".format('p'*repeat, freq)


async def _play(rtttlstr):
    """
    RTTTL Piezzo Player with async job
    :param rtttlstr str: rttl string, default: 'd=4,o=5,b=250:e,8p,8f,8g,8p,1c6,8p.,d,8p,8e,1f,p.'
    :return str: verdict
    """
    # https://github.com/dhylands/upy-rtttl/blob/master/songs.py
    tune = RTTTL(rtttlstr)
    with micro_task(tag=__TASK_TAG) as task:
        task.out = "Play song..."
        for freq, msec in tune.notes():
            __play_tone(freq, msec)
            await asyncio.sleep_ms(40)
        task.out = "Song played successfully"
    del tune


def play(rtttlstr='d=4,o=5,b=250:e,8p,8f,8g,8p,1c6,8p.,d,8p,8e,1f,p.'):
    """
    RTTTL Piezzo Player
    :param rtttlstr str: rttl string, default: 'd=4,o=5,b=250:e,8p,8f,8g,8p,1c6,8p.,d,8p,8e,1f,p.'
    :return str: verdict
    """
    state = micro_task(tag=__TASK_TAG, task=_play(rtttlstr))
    if state:
        return 'Play song'
    return 'Song already playing'


def load_n_init(cache=None):
    """
    Initiate buzzer module
    :param cache bool: file state machine cache: True/False/None(default: automatic True)
    - Load .pds (state machine cache) for this load module
    - Apply loaded states to gpio pins (boot function)
    :return str: Cache state
    """
    from sys import platform
    global __PERSISTENT_CACHE
    if cache is None:
        __PERSISTENT_CACHE = False if platform == 'esp8266' else True
    else:
        __PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')
    return "CACHE: {}".format(__PERSISTENT_CACHE)


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
    return pinmap_dump('buzzer')


def help():
    """
    [i] micrOS LM naming convention
    Load Module built-in help message
    :return tuple: list of functions implemented by this application
    """
    return 'bipp repeat=<int> freq=<Hz>', 'play <rtttlstr>', 'load_n_init', 'pinmap'
