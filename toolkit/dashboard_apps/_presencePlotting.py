#!usr/bin/env python3

import sys
import os
from numpy import average
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import ast

MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(MYPATH))
import socketClient

sys.path.append(os.path.join(MYPATH, "../lib/"))

# FILL OUT
DEVICE = "node01"
MA_SIZE = 5  # size of moving average, should be the same as buff_size to appear accurately


def base_cmd():
    return ["--dev", DEVICE]


def measure(x, y, trigger_x, trigger_y):
    """
    x, y: timestamp and amplitude
    trigger_x, trigger_y: timestamp and trigger value
    Query the buffered amplitude values combined with the trigger events
    """
    args = base_cmd() + ["presence get_samples >json"]

    try:
        status, answer = socketClient.run(args)
    except Exception as e:
        print(e.msg)
        return x, y

    if status:
        last = x[-1] if len(x) > 0 else 0

        # Avoid overlapping by filtering timestamps
        for d in filter(lambda d: d[0] > last, ast.literal_eval(answer)):
            x.append(d[0])
            y.append(d[1])
            # Add trigger points if the trigger value is positive
            if d[2] > 0:
                trigger_x.append(d[0])
                trigger_y.append(d[1])
    else:
        return None


def plotting(frames, window_size, repeat):
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    x = []
    y = []
    trigger_x = []
    trigger_y = []

    def update(i):

        # Measure data, clear plot
        measure(x, y, trigger_x, trigger_y)
        ax.clear()

        # Moving average
        ma = [average(y[i - MA_SIZE : i]) for i in range(MA_SIZE, len(x))]

        # Plot
        ax.plot(x, y, label="amplitude")
        ax.plot(x[MA_SIZE:], ma, label="amplitude (moving average)")
        ax.scatter(trigger_x, trigger_y, color="red", label="trigger events")

        # Plot formatting
        ax.set_title('Microphone amplitude', fontsize=12, fontweight='bold')
        ax.set_ylabel("Intensity (0-100)")
        ax.set_xlabel("Timestamp")
        ax.legend()
        ax.grid()

        # Set limits (only display a section with a size of 'window_size')
        ax.set_ylim(bottom=0, top=100)
        if len(x):
            ax.set_xlim(left=(x[0] if len(x) <= window_size else x[-window_size]), right=x[-1])

        # Debug: calculate min, max, avg sampling frequency on the current time window
        raw_sample = 15     # on device sampling average (TODO: dynamic!)
        if len(x):
            diffs = [abs(x[i] - x[i - 1]) for i in range(-min(len(x) - 1, window_size), 0)]
            ax.text(0.01, 0.02,
                    "Avg(${f_{sampling}}$) [Hz] = "f"{1/(average(diffs)/1000):.2f}" 
                    "\nMin(${f_{sampling}}$) [Hz] = "f"{1/(max(diffs)/1000):.2f}"
                    "\nMax(${f_{sampling}}$) [Hz] = "f"{1/(min(diffs)/1000):.2f}"
                    "\nAvgRaw(${f_{sampling}}$) [Hz] = "f"{(1/(average(diffs)/1000))*raw_sample:.2f}",
                    transform=ax.transAxes,
                    fontsize=10
                    )

    a = anim.FuncAnimation(fig, update, frames=frames, repeat=repeat)
    plt.show()


def app(devfid=None):
    """
    devfid: selected device input
    frames: number of measurements to take
    window_size: maximum number of data points displayed at once
    repeat: measure continuously
    """
    global DEVICE

    # Handle command line arguments
    args = sys.argv
    print("Start python script: {}".format(args[0]))
    if len(args) > 1:
        devfid = args[1]

    if devfid is not None:
        DEVICE = devfid

    plotting(frames=100, window_size=200, repeat=True)


if __name__ == "__main__":
    app()

