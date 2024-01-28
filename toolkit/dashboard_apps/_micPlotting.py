#!usr/bin/env python3

import sys
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import io
import soundfile as sf
import numpy as np
import re
import urllib3
import threading
import time

from collections import deque

RECORD = True           # Indiciate if threads should be terminated
STREAM_THREAD = None    # Thread for processing the multipart stream
DECODING_THREAD = None  # Thread for decoding raw bytes

SAMPLE_RATE = None
NUM_CHANNELS = None
RAW_DATA = deque()      # Raw data (bytes) passed from HTTP stream
AUDIO_DATA = []         # Decoded audio for visualization
AUDIO_DATA_BYTES = []   # Audio data in byte format, to be saved as a file
ENCODING = 'PCM_16'
READ_SIZE = 8192


def create_multipart_stream(url):
    stream = urllib3.request('GET',url,preload_content=False)
    reader = io.BufferedReader(stream)
    return reader


def run_stream(reader):
    global RAW_DATA
    global NUM_CHANNELS
    global SAMPLE_RATE

    while RECORD:
        current_line = reader.readline(READ_SIZE).rstrip(b'\r\n')
        boundary = current_line.find(b'--micrOS_boundary')
        header = current_line.find(b'Content-Type: audio/l16')

        if header != -1 and (not SAMPLE_RATE or not NUM_CHANNELS):
            # Determine sampling parameters from content-type
            m_r = re.search(b'rate=(\d+)', current_line)
            m_c = re.search(b'channels=(\d)', current_line)
            if not m_r or not m_c:
                raise Exception('Invalid content-type, could not determine sample rates or channels.')
            SAMPLE_RATE = int(m_r.group(1))
            NUM_CHANNELS = int(m_c.group(1))
            print(f'Sampling rate: {SAMPLE_RATE}, number of channels: {NUM_CHANNELS}')

        if len(current_line) and boundary == -1 and header == -1:
            # The line contains audio data
            RAW_DATA.append(current_line)


# Decode audio bytes (PCM_16) to floats (-1 to 1)
def decode_audio_bytes(audio_bytes):
    data, _ = sf.read(io.BytesIO(audio_bytes),
                      format='RAW',
                      samplerate=SAMPLE_RATE,
                      channels=NUM_CHANNELS,
                      subtype=ENCODING,
                      endian='LITTLE')
    return data


def decode_audio():
    global RAW_DATA
    global AUDIO_DATA
    global AUDIO_DATA_BYTES

    while RECORD:
        counter = 10 # How many segments to process at once
        while len(RAW_DATA) and counter > 0:
            new_data = RAW_DATA.popleft()
            AUDIO_DATA_BYTES.extend(new_data)
            AUDIO_DATA.extend(decode_audio_bytes(new_data))
            counter -= 1
        time.sleep(0.01)


def start_stream(url):
    global STREAM_THREAD
    global DECODING_THREAD

    fig, ax = plt.subplots()
    stream = create_multipart_stream(url)
    STREAM_THREAD = threading.Thread(target=run_stream, args=(stream,))
    STREAM_THREAD.start()
    DECODING_THREAD = threading.Thread(target=decode_audio)
    DECODING_THREAD.start()

    def update(i):
        current_length = len(AUDIO_DATA)
        if current_length:
            ax.clear()
            plt.plot(range(current_length), AUDIO_DATA[:current_length])
            plt.grid()
            plt.ylim([-1*np.max(AUDIO_DATA[:current_length])*1.3,np.max(AUDIO_DATA[:current_length])*1.3])
            plt.xlim([current_length-SAMPLE_RATE*3,current_length])
            plt.title('Microphone recording', fontsize=12, fontweight='bold')
            plt.ylabel("Amplitude")
            plt.xlabel("Sample")

            ax.text(0.01, 0.02,
                "${f_{sampling}}$ [Hz] = "f"{SAMPLE_RATE:.2f}",
                transform=ax.transAxes,
                fontsize=10
                )

    ani = anim.FuncAnimation(fig, update, repeat=True, interval=50)
    plt.show()


def app(devfid=None):
    """
    devfid: selected device input
    frames: number of measurements to take
    window_size: maximum number of data points displayed at once
    repeat: measure continuously
    """
    global RECORD

    # Handle command line arguments
    args = sys.argv
    print("Start python script: {}".format(args[0]))
    devfid = '10.0.1.106'       # Default for test

    if len(args) > 1:
        devfid = args[1]

    url = f"http://{devfid}/mic/stream"
    start_stream(url)
    RECORD = False
    STREAM_THREAD.join()
    DECODING_THREAD.join()


if __name__ == "__main__":
    app()
    if len(AUDIO_DATA):
        wav_file = f'./toolkit/user_data/{int(time.time()*1000)}.wav'
        sf.write(file=wav_file,
                 data=AUDIO_DATA,
                 format='WAV',
                 samplerate=SAMPLE_RATE,
                 subtype=ENCODING,
                 endian='LITTLE')
        print(f'WAV file saved to: {wav_file}')
