from ustruct import unpack
from microIO import bind_pin, pinmap_search
from Common import micro_task, web_endpoint, manage_task
from machine import I2S, Pin
import uasyncio as asyncio


class Data:
    SCK_PIN = Pin(bind_pin('i2s_sck'))  # Serial clock
    WS_PIN = Pin(bind_pin('i2s_ws'))    # Word select
    SD_PIN = Pin(bind_pin('i2s_sd'))    # Serial data
    I2S_CHANNEL = 1
    FORMAT = I2S.STEREO
    SAMPLING_RATE = 8000
    BUF_LENGTH = 16000
    SAMPLE_SIZE = 16
    CAPTURE_DURATION = 0.25
    DEFAULT_CHANNEL = 'right' # right, left, all
    DOWNSAMPLING = 1
    SHIFT_SIZE = 6

    # Microphone control
    MIC_ENABLED = True
    CONTROL_TASK_TAG = 'i2s._mic_control'
    CONTROL_BUTTON_PIN = None

    # To be initialized by load
    I2S_AUDIO_IN = None
    SREADER = None

    # Only used by micro task
    TASK_TAG = 'i2s._mic'
    MIC_SAMPLES = bytearray()
    RECORD_TASK_ENABLED = False


##################
# Button control #
##################
    
# Micro task is used to debounce button press instead of IRQ.
# This also gives more control over determining how the button is pressed.

async def __control_task(ms_period=50):
    """
    Microphone kill switch task.
    By pressing the button, the capture task will be terminated.
    Different load modules will only get an empty byte array when
    querying samples. Pushing the button again reinitializes the
    microphone without having to restart dependent load modules.
    """
    with micro_task(tag=Data.CONTROL_TASK_TAG) as my_task:
        while True:
            if Data.CONTROL_BUTTON_PIN.value():
                Data.MIC_ENABLED = not Data.MIC_ENABLED
                print(f'Microphone enabled: {Data.MIC_ENABLED}')

                if Data.MIC_ENABLED:
                    load()

                # Debounce
                await my_task.feed(sleep_ms=500)
            await my_task.feed(sleep_ms=ms_period)


###########################
# Capturing by micro task #
###########################

async def __task(ms_period):
    with micro_task(tag=Data.TASK_TAG) as recording_task:
        Data.RECORD_TASK_ENABLED = True
        try:
            Data.MIC_SAMPLES = bytearray(bytes_per_second(Data.CAPTURE_DURATION))
            sample_mv = memoryview(Data.MIC_SAMPLES)
            recording_task.out = 'Capturing'
            while Data.MIC_ENABLED:
                await Data.SREADER.readinto(sample_mv)
                await recording_task.feed(sleep_ms=ms_period)
            recording_task.out = 'Finished'

        except Exception as e:
            Data.RECORD_TASK_ENABLED = False
            recording_task.out = f'Failed: {e}'

        finally:
            Data.MIC_SAMPLES = bytearray()


def background_capture():
    """
    Start recording samples into a buffer by micro task
    """
    if not Data.MIC_ENABLED:
        return "Microphone is disabled"

    state = micro_task(tag=Data.TASK_TAG, task=__task(ms_period=1))
    return "Starting" if state else "Already running"


def get_from_buffer(capture_duration=Data.CAPTURE_DURATION,
                    channel = Data.DEFAULT_CHANNEL,
                    downsampling=Data.DOWNSAMPLING):
    """
    Return samples stored in the buffer, captured by micro task
    :capture_duration: maximum duration (seconds) of samples to retrieve (number)
    :channel: which channel to get samples from ('left', 'right' or 'all')
    :downsampling: return every nth sample (int)
    """
    if not Data.MIC_ENABLED:
        return bytearray()

    num_samples = bytes_per_second(capture_duration)
    num_samples = min(num_samples, len(Data.MIC_SAMPLES))
    samples = bytearray(num_samples)
    samples[:] = Data.MIC_SAMPLES[:num_samples]
    
    if Data.SHIFT_SIZE:
        samples_mv = memoryview(samples)
        I2S.shift(buf=samples_mv,shift=Data.SHIFT_SIZE,bits=Data.SAMPLE_SIZE)

    return select_channel(samples, channel, downsampling)


###########################
# Asnyc capturing methods #
###########################

async def _capture(capture_duration = Data.CAPTURE_DURATION,
                  downsampling = Data.DOWNSAMPLING):
    """
    Capture and return an array of samples asynchronously (without micro task)
    Can be used to reliably capture large samples without overlapping segments
    :capture_duration: maximum duration (seconds) of samples to retrieve (number)
    :downsampling: return every nth sample (int)
    """
    if not Data.MIC_ENABLED:
        return bytearray()
    
    if manage_task(Data.TASK_TAG, 'isbusy'):
        print('[i2s_mic] Warning: micro task is already running, capturing directly is not possible. '\
                      'Use get_from_buffer() instead.')
        return bytearray()

    mic_samples = bytearray(bytes_per_second(capture_duration))
    sample_mv = memoryview(mic_samples)
    num_read = await Data.SREADER.readinto(sample_mv)

    if Data.SHIFT_SIZE:
        I2S.shift(buf=sample_mv,shift=Data.SHIFT_SIZE,bits=Data.SAMPLE_SIZE)

    return select_channel(mic_samples[:num_read], Data.DEFAULT_CHANNEL, downsampling)


def _record_clb():
    """
    Callback for HTTP API request
    """
    # TODO: add encoding/compression for different MIME types
    # Currently, audio/l16 is supported (uncompressed, signed 16-bit, twos-complement)
    # audio/l16 MIME type: https://www.rfc-editor.org/rfc/rfc2586
    num_channels = 2 if Data.DEFAULT_CHANNEL == 'all' and Data.FORMAT == I2S.STEREO else 1
    if Data.SAMPLE_SIZE != 16:
        return 'text/plain', f'Invalid sample size configured. 16-bit representation must be used.'
    
    return 'multipart/form-data', \
        {'callback': _capture, 'content-type': f'audio/l16;rate={Data.SAMPLING_RATE};channels={num_channels}'}


####################
# Common functions #
####################

def select_channel(samples=b'', channel = Data.DEFAULT_CHANNEL, downsampling = 1):
    """
    Separate channels from stereo data and/or apply downsampling
    Can be used as a workaround for https://github.com/espressif/esp-idf/issues/6625
    :samples: samples to select channels from (bytes, bytearray)
    :channel: which channel to get samples from ('left', 'right' or 'all')
    :downsampling: return every nth sample (int)
    """
    sample_size_bytes = int(Data.SAMPLE_SIZE / 8)
    if channel == 'left' and Data.FORMAT == I2S.STEREO:     # Left channel with or without downsampling
        offset = 0
        step = 2 * sample_size_bytes * downsampling
    elif channel == 'right' and Data.FORMAT == I2S.STEREO:  # Right channel with or without downsampling
        offset = sample_size_bytes
        step = 2 * sample_size_bytes * downsampling
    elif downsampling > 1 and Data.FORMAT == I2S.STEREO:    # All channels with downsampling
        offset = 0
        sample_size_bytes *= 2
        step = sample_size_bytes * downsampling
    elif downsampling > 1 and Data.FORMAT == I2S.MONO:      # One channel with downsampling
        offset = 0
        step = sample_size_bytes * downsampling
    else:                                                   # One or both channels without downsampling
        return samples

    selected = bytearray()

    for i in range(offset, len(samples) - sample_size_bytes + 1, step):
        selected.extend(samples[i:i+sample_size_bytes])
    
    return selected


def decode(samples=b''):
    """
    Decode raw bytes to floats between -1 and 1
    :samples: samples to select channels from (bytes, bytearray)
    """
    samples_decoded = []

    sample_size_bytes = int(Data.SAMPLE_SIZE / 8)
    offset = 0
    step = 1 * sample_size_bytes

    if Data.SAMPLE_SIZE == 16:
        unpack_format = "<h" 
    elif Data.SAMPLE_SIZE == 32:
        unpack_format = "<hh"

    for i in range(offset, len(samples), step):
        if i+sample_size_bytes <= len(samples):
            sample_int = unpack(unpack_format, samples[i:i+sample_size_bytes])[0]
            samples_decoded.append((sample_int+1)/(2**(Data.SAMPLE_SIZE-1)))

    return samples_decoded


def bytes_per_second(t=1):
    """
    Get configured number of bytes per second
    :t: seconds (number)
    """
    num_channels = 2 if Data.FORMAT == I2S.STEREO else 1
    return int(Data.SAMPLING_RATE * num_channels * (Data.SAMPLE_SIZE / 8) * t)


def set_volume(shift_size=0):
    """
    Change default volume by positive/negative bitwise shift
    :param mic: shift_size, positive shift increases volume (int)
    """
    Data.SHIFT_SIZE = shift_size


def load(buf_length=Data.BUF_LENGTH, sampling_rate=Data.SAMPLING_RATE,
                capture_duration=Data.CAPTURE_DURATION, shift_size = Data.SHIFT_SIZE,
                sample_size = Data.SAMPLE_SIZE, i2s_channel = Data.I2S_CHANNEL,
                default_channel = Data.DEFAULT_CHANNEL, sound_format = Data.FORMAT,
                downsampling = Data.DOWNSAMPLING, control_button='',
                enable_endpoint = True):
    """
    Initialize I2S microphone module
    :buf_length: I2S internal buffer length (int)
    :sampling_rate: I2S sampling rate (int)
    :capture_duration: override default duration of samples to retrieve
    :shift_size: override default shift size
    :sample_size: override default sample size (16 or 32)
    :i2s_channel: override default I2S channel
    :default_channel: override default channel ('left', 'right' or 'all')
    :sound_format: override default format (I2S.MONO, I2S.STEREO)
    :downsampling: override default downsampling
    :control_button: name of button pin, control task is enbaled when provided
    :enable_endpoint: enable/disable endpoint creation at /mic/stream (True/False)
    """
    if sample_size not in (16,32):
        return f'Invalid samples size {sample_size}. Must be either 16 or 32.'
    
    if default_channel not in ('left', 'right', 'all'):
        return f'Invalid channel. Must be one of \'left\', \'right\', \'all\'.'
    
    if sound_format not in (I2S.MONO, I2S.STEREO):
        return f'Invalid format. Must either be I2S.MONO (0) or I2S.STEREO (1).'
    
    if control_button:
        micro_task(tag=Data.CONTROL_TASK_TAG, task=__control_task())
        Data.CONTROL_BUTTON_PIN = Pin(bind_pin(control_button), Pin.IN)

    Data.BUF_LENGTH = buf_length
    Data.SAMPLING_RATE = sampling_rate
    Data.CAPTURE_DURATION = capture_duration
    Data.SHIFT_SIZE = shift_size
    Data.SAMPLE_SIZE = sample_size
    Data.I2S_CHANNEL = i2s_channel
    Data.FORMAT = sound_format
    Data.DEFAULT_CHANNEL = default_channel
    Data.DOWNSAMPLING = downsampling

    Data.I2S_AUDIO_IN = I2S(Data.I2S_CHANNEL,sck=Data.SCK_PIN, ws=Data.WS_PIN,
                    sd=Data.SD_PIN,mode=I2S.RX,bits=Data.SAMPLE_SIZE,
                    format=Data.FORMAT,rate=Data.SAMPLING_RATE,ibuf=Data.BUF_LENGTH)
    Data.SREADER = asyncio.StreamReader(Data.I2S_AUDIO_IN)

    if enable_endpoint:
        web_endpoint('mic/stream', _record_clb)

    if Data.RECORD_TASK_ENABLED:
        background_capture()

    return "Init I2S microphone on channel {}".format(i2s_channel)


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
    return pinmap_search(['i2s_sck', 'i2s_ws', 'i2s_sd'])


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'load buf_length=16000 '\
           'sampling_rate=8000 capture_duration=0.25 shift_size=6 '\
           'sample_size=16 i2s_channel=1 default_channel=\'right\' '\
           'sound_format=I2S.STEREO downsampling=1 control_button='' enable_endpoint=True',\
           'background_capture',\
           'get_from_buffer capture_duration=1 channel=\'right\' downsampling=1',\
           'capture capture_duration=1 channel=\'right\' downsampling=1',\
           'select_channel samples=b\'\' channel=\'right\' downsampling=1',\
           'decode samples=b\'\'',\
           'bytes_per_second t=1',\
           'set_volume shift_size=0',\
           'pinmap'
