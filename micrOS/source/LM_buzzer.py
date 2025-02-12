from sys import platform
from utime import sleep
from microIO import bind_pin, pinmap_search
from Common import micro_task, notify
from Types import resolve


#########################################
#      BUZZER PWM CONTROLLER PARAMS     #
#########################################
__BUZZER_OBJ = None
# DATA: state:ON/OFF, freq:0-1000
__BUZZER_CACHE = [600]
__PERSISTENT_CACHE = False
__TASK_TAG = "buzzer._play"
CHECK_NOTIFY = False

#########################################
#              BUZZER RTTL              #
#########################################

NOTE = (
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
    0.0
)


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


def _builtin_tones(tone=None):
    tones = (
        ("Indiana", "d=4,o=5,b=250:e,8p,8f,8g,8p,1c6,8p.,d,8p,8e,1f,p.,g,8p,8a,8b,8p,1f6,p,a,8p,8b,2c6,2d6,2e6,e,8p,8f,8g,8p,1c6,p,d6,8p,8e6,1f.6,g,8p,8g,e.6,8p,d6,8p,8g,e.6,8p,d6,8p,8g,f.6,8p,e6,8p,8d6,2c6"),
        ("TakeOnMe", "d=4,o=4,b=160:8f#5,8f#5,8f#5,8d5,8p,8b,8p,8e5,8p,8e5,8p,8e5,8g#5,8g#5,8a5,8b5,8a5,8a5,8a5,8e5,8p,8d5,8p,8f#5,8p,8f#5,8p,8f#5,8e5,8e5,8f#5,8e5,8f#5,8f#5,8f#5,8d5,8p,8b,8p,8e5,8p,8e5,8p,8e5,8g#5,8g#5,8a5,8b5,8a5,8a5,8a5,8e5,8p,8d5,8p,8f#5,8p,8f#5,8p,8f#5,8e5,8e5"),
        ("Entertainer", "d=4,o=5,b=140:8d,8d#,8e,c6,8e,c6,8e,2c.6,8c6,8d6,8d#6,8e6,8c6,8d6,e6,8b,d6,2c6,p,8d,8d#,8e,c6,8e,c6,8e,2c.6,8p,8a,8g,8f#,8a,8c6,e6,8d6,8c6,8a,2d6"),
        ("Xfiles", "d=4,o=5,b=125:e,b,a,b,d6,2b.,1p,e,b,a,b,e6,2b.,1p,g6,f#6,e6,d6,e6,2b.,1p,g6,f#6,e6,d6,f#6,2b.,1p,e,b,a,b,d6,2b.,1p,e,b,a,b,e6,2b.,1p,e6,2b."),
        ("20thCenFox", "d=16,o=5,b=140:b,8p,b,b,2b,p,c6,32p,b,32p,c6,32p,b,32p,c6,32p,b,8p,b,b,b,32p,b,32p,b,32p,b,32p,b,32p,b,32p,b,32p,g#,32p,a,32p,b,8p,b,b,2b,4p,8e,8g#,8b,1c#6,8f#,8a,8c#6,1e6,8a,8c#6,8e6,1e6,8b,8g#,8a,2b"),
        ("Bond", "d=4,o=5,b=80:32p,16c#6,32d#6,32d#6,16d#6,8d#6,16c#6,16c#6,16c#6,16c#6,32e6,32e6,16e6,8e6,16d#6,16d#6,16d#6,16c#6,32d#6,32d#6,16d#6,8d#6,16c#6,16c#6,16c#6,16c#6,32e6,32e6,16e6,8e6,16d#6,16d6,16c#6,16c#7,c.7,16g#6,16f#6,g#.6"),
        ("StarWars", "d=4,o=5,b=45:32p,32f#,32f#,32f#,8b.,8f#.6,32e6,32d#6,32c#6,8b.6,16f#.6,32e6,32d#6,32c#6,8b.6,16f#.6,32e6,32d#6,32e6,8c#.6,32f#,32f#,32f#,8b.,8f#.6,32e6,32d#6,32c#6,8b.6,16f#.6,32e6,32d#6,32c#6,8b.6,16f#.6,32e6,32d#6,32e6,8c#6"),
        ("A-Team", "d=8,o=5,b=125:4d#6,a#,2d#6,16p,g#,4a#,4d#.,p,16g,16a#,d#6,a#,f6,2d#6,16p,c#.6,16c6,16a#,g#.,2a#"),
        ("Flinstones", "d=4,o=5,b=40:32p,16f6,16a#,16a#6,32g6,16f6,16a#.,16f6,32d#6,32d6,32d6,32d#6,32f6,16a#,16c6,d6,16f6,16a#.,16a#6,32g6,16f6,16a#.,32f6,32f6,32d#6,32d6,32d6,32d#6,32f6,16a#,16c6,a#,16a6,16d.6,16a#6,32a6,32a6,32g6,32f#6,32a6,8g6,16g6,16c.6,32a6,32a6,32g6,32g6,32f6,32e6,32g6,8f6,16f6,16a#.,16a#6,32g6,16f6,16a#.,16f6,32d#6,32d6,32d6,32d#6,32f6,16a#,16c.6,32d6,32d#6,32f6,16a#,16c.6,32d6,32d#6,32f6,16a#6,16c7,8a#.6"),
        ("Smurfs", "d=32,o=5,b=200:4c#6,16p,4f#6,p,16c#6,p,8d#6,p,8b,p,4g#,16p,4c#6,p,16a#,p,8f#,p,8a#,p,4g#,4p,g#,p,a#,p,b,p,c6,p,4c#6,16p,4f#6,p,16c#6,p,8d#6,p,8b,p,4g#,16p,4c#6,p,16a#,p,8b,p,8f,p,4f#"),
        ("MissionImp", "d=16,o=6,b=95:32d,32d#,32d,32d#,32d,32d#,32d,32d#,32d,32d,32d#,32e,32f,32f#,32g,g,8p,g,8p,a#,p,c7,p,g,8p,g,8p,f,p,f#,p,g,8p,g,8p,a#,p,c7,p,g,8p,g,8p,f,p,f#,p,a#,g,2d,32p,a#,g,2c#,32p,a#,g,2c,a#5,8c,2p,32p,a#5,g5,2f#,32p,a#5,g5,2f,32p,a#5,g5,2e,d#,8d"),
        ("smbdeath", "d=4,o=5,b=90:32c6,32c6,32c6,8p,16b,16f6,16p,16f6,16f.6,16e.6,16d6,16c6,16p,16e,16p,16c"),
        ("BarbieGirl", "d=4,o=5,b=125:8g#,8e,8g#,8c#6,a,p,8f#,8d#,8f#,8b,g#,8f#,8e,p,8e,8c#,f#,c#,p,8f#,8e,g#,f#"),
        ("TakeOnMe", "d=4,o=4,b=160:8f#5,8f#5,8f#5,8d5,8p,8b,8p,8e5,8p,8e5,8p,8e5,8g#5,8g#5,8a5,8b5,8a5,8a5,8a5,8e5,8p,8d5,8p,8f#5,8p,8f#5,8p,8f#5,8e5,8e5,8f#5,8e5,8f#5,8f#5,8f#5,8d5,8p,8b,8p,8e5,8p,8e5,8p,8e5,8g#5,8g#5,8a5,8b5,8a5,8a5,8a5,8e5,8p,8d5,8p,8f#5,8p,8f#5,8p,8f#5,8e5,8e5")
    )
    if tone is None:
        # Return list of titles
        return (title[0] for title in tones)
    if tone.startswith('d='):
        # Raw rtttl input return
        return tone
    for builtin in tones:
        if tone.strip().lower() in builtin[0].lower():
            return builtin[1]
    # Tone not found, return default short Indiana...
    return 'd=4,o=5,b=250:e,8p,8f,8g,8p,1c6,8p.,d,8p,8e,1f,p.'

#########################################
#         BUZZER MAIN FUNCTIONS         #
#########################################


def __buzzer_init(pin=None):
    """
    :param pin: optional number to overwrite default pin
    """
    global __BUZZER_OBJ
    if __BUZZER_OBJ is None:
        from machine import Pin, PWM
        dimmer_pin = Pin(bind_pin('buzzer', number=pin))
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
    global __BUZZER_CACHE, CHECK_NOTIFY
    if CHECK_NOTIFY and not notify():
        return "NoBipp - notify off"
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
    :param rtttlstr str: rttl string
    :return str: verdict
    """
    # https://github.com/dhylands/upy-rtttl/blob/master/songs.py
    rtttlstr = _builtin_tones(tone=rtttlstr)
    tune = RTTTL(rtttlstr)
    with micro_task(tag=__TASK_TAG) as task:
        task.out = "Play song..."
        for freq, msec in tune.notes():
            __play_tone(freq, msec)
            await task.feed(sleep_ms=10)
        task.out = "Song played successfully"
    del tune


def play(rtttlstr='Indiana'):
    """
    RTTTL Piezzo Player
    :param rtttlstr str: rttl string, default: 'd=4,o=5,b=250:e,8p,8f,8g,8p,1c6,8p.,d,8p,8e,1f,p.'
    :return str: verdict
    """
    global CHECK_NOTIFY
    if CHECK_NOTIFY and not notify():
        return "NoBipp - notify off"
    state = micro_task(tag=__TASK_TAG, task=_play(rtttlstr))
    if state:
        return 'Play song'
    return 'Song already playing'


def list_tones():
    """
    List built-in tones
    """
    return '\n'.join(list(_builtin_tones()))


def load(check_notify=False, pin=None, cache=True):
    """
    Initialize buzzer module
    :param check_notify: check notify enabled/disabled - make noise if enabled only
    :param pin: optional number to overwrite default pin
    :param cache: default True, store stages on disk (.pds)
    :return str: Verdict
    """
    from sys import platform
    global __PERSISTENT_CACHE, CHECK_NOTIFY
    __PERSISTENT_CACHE = cache
    __persistent_cache_manager('r')
    CHECK_NOTIFY = check_notify
    __buzzer_init(pin=pin)
    return f"CACHE: {__PERSISTENT_CACHE}, check notify: {CHECK_NOTIFY}"


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
    return pinmap_search('buzzer')


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return resolve(('BUTTON bipp repeat=3 freq=600',
                             'BUTTON play rtttlstr=<Indiana,TakeOnMe,StarWars,MissionImp>',
                             'list_tones',
                             'load check_notify=False', 'pinmap'), widgets=widgets)
