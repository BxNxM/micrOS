import sys
import signal

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Timed out!")

def input_with_timeout(prompt, default=None, timeout=5):
    is_windows = True if sys.platform.startswith('win') else False
    if is_windows:
        print("[WARNING] WINDOWS NO TIMEOUT OPTION FOR USER INPUT...")
        return input(prompt)

    try:
        # Set up a signal handler for the alarm signal
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)  # Set the alarm to trigger after timeout
        user_input = input(prompt)
    except Exception as e:
        print(f"Timeout reached. Default value will be used.: {e}")
        user_input = default
    finally:
        # Reset the alarm to 0 to cancel any pending alarms
        signal.alarm(0)
    return user_input

