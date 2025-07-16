import matplotlib.pyplot as plt
import matplotlib.animation as animation
import multiprocessing as mp
from collections import deque
from datetime import datetime
import matplotlib.dates as mdates

def visualizer_main(queue):
    # Make figure wider and a bit taller
    fig, (ax_accel, ax_gyro) = plt.subplots(2, 1, figsize=(14, 8))
    plt.subplots_adjust(top=0.88, bottom=0.12, hspace=0.3)

    history = 100
    accel_data = {'x': deque([0] * history, maxlen=history),
                  'y': deque([0] * history, maxlen=history),
                  'z': deque([0] * history, maxlen=history)}
    gyro_data = {'x': deque([0] * history, maxlen=history),
                 'y': deque([0] * history, maxlen=history),
                 'z': deque([0] * history, maxlen=history)}
    time_axis = deque([datetime.now()] * history, maxlen=history)

    # Increase line width here
    line_width = 2.5

    accel_lines = {
        axis: ax_accel.plot([], [], label=f'accel_{axis}', linewidth=line_width)[0]
        for axis in 'xyz'
    }
    gyro_lines = {
        axis: ax_gyro.plot([], [], label=f'gyro_{axis}', linewidth=line_width)[0]
        for axis in 'xyz'
    }

    ax_accel.set_ylim(-2, 2)
    ax_gyro.set_ylim(-300, 300)

    for ax in [ax_accel, ax_gyro]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax.legend()
        ax.grid(True)
        ax.set_xlabel("Time (H:M:S)")

    ax_accel.set_title("Acceleration")
    ax_gyro.set_title("Gyroscope")

    def update(_):
        try:
            while not queue.empty():
                data = queue.get_nowait()
                current_time = datetime.now()
                time_axis.append(current_time)

                for axis, val in zip('xyz', data['accel']):
                    accel_data[axis].append(val)
                for axis, val in zip('xyz', data['gyro']):
                    gyro_data[axis].append(val)
        except Exception as e:
            print(f"Visualizer error: {e}")
            return

        for axis in 'xyz':
            accel_lines[axis].set_data(time_axis, accel_data[axis])
            gyro_lines[axis].set_data(time_axis, gyro_data[axis])

        for ax in [ax_accel, ax_gyro]:
            ax.set_xlim(time_axis[0], time_axis[-1])
            ax.figure.autofmt_xdate()

        return list(accel_lines.values()) + list(gyro_lines.values())

    ani = animation.FuncAnimation(fig, update, interval=50)
    plt.show()


if __name__ == "__main__":
    mp.set_start_method('spawn')
    queue = mp.Queue()
    visualizer_main(queue)
