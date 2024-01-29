#!usr/bin/env python3

import sys
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import io
import soundfile as sf
import re
import requests
import threading
import time
import pyaudio

from collections import deque

OUTPUT_DEVICE = None    # use pyaudio.PyAudio().get_device_info_by_index(i) to determine non-default output device
ENCODING = 'PCM_16'     # 16-bit PCM is used for audio/l16
PLOT_INTERVAL_MS = 50   # iterval between plot updates
PLOT_MAX_LEN = 40000    # maximum number of samples to display on the plot
MULTIPART_BOUNDARY = b'\r\n--micrOS_boundary\r\n'   # multipart boundary to search for when reading the stream


def determine_parameters(reader):
    retry_counter = 100
    for line in reader:
        if retry_counter <= 0:
            break

        retry_counter -= 1
        header = line.find(b'Content-Type: audio/l16')

        if header == -1:
            continue

        # Determine sampling parameters from content-type
        m_r = re.search(b'rate=(\d+)', line)
        m_c = re.search(b'channels=(\d)', line)

        if not m_r or not m_c:
            raise Exception('Invalid content-type, could not determine sample rates or channels.')

        sample_rate = int(m_r.group(1))
        num_channels = int(m_c.group(1))

        print(f'Sampling rate: {sample_rate}, number of channels: {num_channels}')

        # Play live audio on the device corresponding to OUTPUT_DEVICE index
        pyaudio_player = pyaudio.PyAudio()
        pyaudio_stream = pyaudio_player.open(format=pyaudio.paInt16,
                                                channels=num_channels,
                                                rate=sample_rate,
                                                output_device_index=OUTPUT_DEVICE,
                                                output=True)

        return sample_rate, num_channels, pyaudio_player, pyaudio_stream
    raise Exception('Could not determine sampling parameters')


def run_stream(reader, terminate_event, raw_data_queue):
    """
    Read multipart stream
    """
    for line in reader:
        line = line.lstrip(b'Content-Type: audio/l16;rate=8000;channels=1\r\n\r\n')
        if len(line):
            raw_data_queue.append(line)

        if terminate_event.is_set():
            break


def decode_audio_bytes(audio_bytes, sample_rate, num_channels, encoding):
    """
    Decode audio bytes (PCM_16) to floats (-1 to 1)
    """
    data, _ = sf.read(io.BytesIO(audio_bytes),
                      format='RAW',
                      samplerate=sample_rate,
                      channels=num_channels,
                      subtype=encoding,
                      endian='LITTLE')
    return data


def decode_audio(terminate_event, raw_data_queue, raw_audio, decoded_audio,
                 sample_rate, num_channels, encoding, pyaudio_stream):
    while not terminate_event.is_set():
        counter = 100 # How many segments to process at once

        new_segment = bytes()
        while len(raw_data_queue) and counter > 0:
            new_segment += raw_data_queue.popleft()
            counter -= 1

        if pyaudio_stream is not None and pyaudio_stream.is_active():
            pyaudio_stream.write(new_segment)

        raw_audio.extend(new_segment)
        decoded_audio.extend(decode_audio_bytes(new_segment, sample_rate, num_channels, encoding))


def start_stream(reader):
    sample_rate, num_channels, pyaudio_player, pyaudio_stream = determine_parameters(reader)

    terminate_event = threading.Event()         # Event object for terminating threads
    raw_data_queue = deque()                    # Raw data (bytes) passed from HTTP stream
    decoded_audio = deque(maxlen=PLOT_MAX_LEN)  # Decoded audio for visualization
    raw_audio = bytearray()                     # Audio data in byte format, to be saved as a file

    # Thread for processing the multipart stream
    stream_thread = threading.Thread(target=run_stream,
                                     args=(reader, terminate_event, raw_data_queue))
    stream_thread.start()

    # Thread for decoding raw bytes
    decoding_thread = threading.Thread(target=decode_audio,
                                       args=(terminate_event, raw_data_queue,
                                             raw_audio, decoded_audio,
                                             sample_rate, num_channels,
                                             ENCODING, pyaudio_stream))
    decoding_thread.start()

    # Plotting animation
    fig, ax = plt.subplots()

    def update(i):
        if len(decoded_audio):
            ax.clear()
            plt.plot(range(len(decoded_audio)), decoded_audio)
            plt.grid()
            plt.ylim([-1,1])
            plt.title('Audio waveform', fontsize=12, fontweight='bold')
            plt.ylabel("Amplitude")
            plt.xlabel("Sample")

            ax.text(0.01, 0.02,
                "${f_{sampling}}$ [Hz] = "f"{sample_rate:.2f}",
                transform=ax.transAxes,
                fontsize=10
                )

    animation = anim.FuncAnimation(fig, update, repeat=True, interval=PLOT_INTERVAL_MS)
    plt.show()

    # Terminate threads and streams when the user closes the window
    terminate_event.set()
    stream_thread.join()
    decoding_thread.join()
    pyaudio_player.terminate()
    pyaudio_stream.stop_stream()
    pyaudio_stream.close()

    # Save recorded audio into a WAV file
    if len(decoded_audio):
        wav_file = f'./toolkit/user_data/{int(time.time()*1000)}.wav'
        sf.write(file=wav_file,
                 data=decode_audio_bytes(raw_audio, sample_rate, num_channels, ENCODING),
                 format='WAV',
                 samplerate=sample_rate,
                 subtype=ENCODING,
                 endian='LITTLE')
        print(f'WAV file saved to: {wav_file}')


def app(devfid=None):
    """
    devfid: selected device input
    """
    # Handle command line arguments
    args = sys.argv
    print("Start python script: {}".format(args[0]))
    devfid = '10.0.1.106'       # Default for test

    if len(args) > 1:
        devfid = args[1]

    url = f"http://{devfid}/mic/stream"

    stream = requests.get(url,stream=True)
    reader = stream.iter_lines(delimiter=MULTIPART_BOUNDARY)
    try:
        start_stream(reader)
    finally:
        stream.close()


if __name__ == "__main__":
    app()
