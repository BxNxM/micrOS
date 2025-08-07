"""
micrOS Load Module programming Official API-s
    Designed by Marcell Ban aka BxNxM
"""
from Server import Server, WebCli
from Debug import syslog as debug_syslog, console_write
from Logger import logger, log_get
from Files import OSPath, path_join
from microIO import resolve_pin
from Tasks import TaskBase, Manager, lm_exec
from machine import Pin, ADC
from Notify import Notify


#####################################################################################
#                                     SYSTEM                                        #
#####################################################################################

def micro_task(tag:str, task=None):
    """
    [LM] Async task manager.
    :param tag: task tag string
    :param task: coroutine (or list of command arguments) to contract a task with the given async task callback
    return bool|callable
    """
    if task is None:
        # [1] Task is None -> Get task mode by tag
        # RETURN task obj (access obj.out + obj.done (automatic - with keyword arg))
        async_task = TaskBase.TASKS.get(tag, None)
        return async_task
    if TaskBase.is_busy(tag):
        # [2] Shortcut: Check task state by tag
        # RETURN: None - if task is already running
        return None
    # [3] Create task (not running) + task coroutine was provided
    # RETURN task creation state - success (True) / fail (False)
    state:bool = Manager().create_task(callback=task, tag=tag)
    return state


def manage_task(tag:str, operation:str):
    """
    [LM] Async task management
    :param tag: task tag
    :param operation: kill / show / isbusy
    """
    if Manager is None:
        # RETURN: None - cannot utilize async task functionality
        return None
    if operation == "show":
        return str(Manager().show(tag=tag))
    if operation == "kill":
        return Manager().kill(tag=tag)
    if operation == "isbusy":
        return TaskBase.is_busy(tag=tag)
    raise Exception(f"Invalid operation: {operation}")


def exec_cmd(cmd:list, jsonify:bool=None, skip_check=None):
    """
    [LM] Single (sync) LM execution
    :param cmd: command string list, ex.: ['system', 'clock']
    :param jsonify: request json output
    :param skip_check: legacy (check was removed) - remove parameter
    return state, output
    """
    return lm_exec(cmd, jsonify=jsonify)


def notify(text=None) -> bool:
    """
    [LM] micrOS common notification handler (Telegram)
    :param text: notification text / None (return notification state)
    return: verdict: True/False
    """
    # (1) Return notification state
    if text is None:
        return Notify.GLOBAL_NOTIFY
    # (2) Send notification
    try:
        out = Notify.notify(text)
    except Exception as e:
        debug_syslog(f"[ERR] Notify: {e}")
        out = str(e)
    if out is not None and (out.startswith('Sent') or out.endswith('disabled')):
        return True
    return False


def web_endpoint(endpoint, function) -> bool:
    """
    [LM] Add test endpoint <localhost.local>/endpoint from Load Modules
    :param endpoint: simple string, name of the endpoint
    :param function:
        [1] Normal function return tuple (html_type, data):
            image/jpeg | text/html | text/plain, <data>
                                                 <data>: binary | string
        [2] Stream function return tuple (multipart_type, data):
            multipart/x-mixed-replace | multipart/form-data, <data>
                <data>: {'callback':<func>, 'content-type': image/jpeg | audio/l16;*}
    """
    WebCli.register(endpoint=endpoint, callback=function)
    return True


def socket_stream(func):
    """
    [LM] Decorator for Socket message stream - adds msgobj to the decorated function arg list.
    Use msgobj as print function: msgobj("hello")
    (Server singleton class - reply all bug/feature)
    """
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs, msgobj=Server.reply_all)
    return wrapper


@socket_stream
def data_logger(f_name, data=None, limit=12, msgobj=None):
    """
    [LM] micrOS Common Data logger solution
    - if data None => read mode
    - if data value => write mode
    :param f_name: log name (without extension, automatic: .dat)
    :param data: data to append
    :param limit: line limit (max.: 12 with short lines: limited disk speed!)
    :param msgobj: socket stream object (set automatically!)
    """
    f_name = f_name if f_name.endswith('.dat') else f'{f_name}.dat'
    # GET LOGGED DATA
    if data is None:
        # return log as msg stream
        log_get(f_name, msgobj=msgobj)
        return True
    # ADD DATA TO LOG
    return logger(data, f_name, limit)


def syslog(msg):
    """ Wrapper of debug_syslog """
    return debug_syslog(f"{msg}")


def console(msg):
    """ Wrapper of console_write """
    return console_write(msg)


def data_dir(f_name=None):
    """
    Access for data dir path
    :param f_name: if given, returns full path, otherwise returns data dir root path
    """
    root_path = OSPath.DATA
    if f_name is None:
        return root_path
    return path_join(root_path, f_name)

def web_dir(f_name=None):
    """
    Access for web dir path
    :param f_name: if given, returns full path, otherwise returns web dir root path
    """
    root_path = OSPath.WEB
    if f_name is None:
        return root_path
    return path_join(root_path, f_name)

#####################################################################################
#                             CHANNEL: SIGNAL GENERATORS                            #
#####################################################################################

def transition(from_val, to_val, step_ms, interval_sec):
    """
    [LM] Single Generator for color/value transition:
    :param from_val: from value - start from
    :param to_val: to value - target value
    :param step_ms: step to reach to_val - timirq_seq
    :param interval_sec: time of full interval
    """
    if interval_sec > 0:
        step_cnt = round((interval_sec*1000)/step_ms)
        delta = abs((from_val-to_val)/step_cnt)
        direc = -1 if from_val > to_val else 1
        for cnt in range(0, step_cnt+1):
            yield round(from_val + (cnt * delta) * direc)
    else:
        yield round(to_val)


def transition_gen(*args, interval_sec=1.0):
    """
    [LM] Multiple Generator for color/value transitions:
    - calculate minimum step count -> step_ms
    - autofill and use transition(from_val, to_val, step_ms, interval_sec)
    :param args: ch1_from, ch1_to, ch2_from, ch2_to, etc...
    :param interval_sec: interval in sec to calculate optimal fade/transition effect
    return: gen, step_ms OR gen list, step_ms
    """
    step_ms_min = 5            # min calculated step is 5 ms - good enough
    delta = max((abs(args[ch_from_i] - args[ch_from_i+1]) for ch_from_i in range(0, len(args)-1, 2)))
    step_ms = 0 if delta == 0 else int(interval_sec*1000 / delta)
    step_ms = step_ms_min if step_ms < step_ms_min else step_ms
    transitions = list((transition(args[ch_from_i], args[ch_from_i+1], step_ms, interval_sec) for ch_from_i in range(0, len(args)-1, 2)))
    if len(transitions) == 1:
        return transitions[0], step_ms
    return list(transitions), step_ms

#####################################################################################
#                                     EXTRAS                                        #
#####################################################################################

class SmartADC:
    """
    [LM] General ADC implementation for auto scaled output: raw, percent, volt
    https://docs.micropython.org/en/latest/esp32/quickref.html#adc-analog-to-digital-conversion
        ADC.ATTN_0DB: 0 dB attenuation, resulting in a full-scale voltage range of 0-1.1V
        ADC.ATTN_2_5DB: 2.5 dB ... of 0-1.5V
        ADC.ATTN_6DB: 6 dB ... of 0-2.2V
        ADC.ATTN_11DB: 11 dB ... of 0-2450mV/
    Note that the absolute maximum voltage rating for input pins is 3.6V. Going near to this boundary risks damage to the IC!
    """
    OBJS = {}

    def __init__(self, pin):
        self.adp_prop = (65535, 2450)                               # raw value, 2450mV (so 2,45V)
        self.adc = None
        if not isinstance(pin, int):
            pin = resolve_pin(pin)
        self.adc = ADC(Pin(pin))
        self.adc.atten(ADC.ATTN_11DB)                               # 2450mV measure range

    def get(self):
        raw = int((self.adc.read_u16() + self.adc.read_u16())/2)    # 16-bit ADC value (0-65535)
        percent = raw / self.adp_prop[0]
        volt = round(percent * self.adp_prop[1] / 1000, 2)          # devide with 1000 to get V from mV
        return {'raw': raw, 'percent': round(percent*100, 1), 'volt': volt}

    @staticmethod
    def get_instance(pin):
        if pin in SmartADC.OBJS.keys():
            return SmartADC.OBJS[pin]
        SmartADC.OBJS[pin] = SmartADC(pin)
        return SmartADC.OBJS[pin]


class AnimationPlayer:
    """
    Generic async animation (generator) player.
    """

    def __init__(self, animation:callable=None, tag:str=None, batch_draw:bool=False, batch_size:int=None, loop:bool=True):
        """
        Initialize the AnimationPlayer with an optional animation.
        :param animation: Function to GENERATE animation data
        :param tag: Optional task tag for micro_task management.
        :param batch_draw: If True - draw in batches
        :param batch_size: Number of pixels per batch when drawing
        :param loop: If True - loop the animation (default)
        """
        self.animation:callable = None
        self.batch_draw:bool = batch_draw
        self.__max_batch_size:int = 256                     # MAX BATCH SIZE - ASYNC PROTECTION
        self.__batch_size:int = 8                           # Default batch size: 8
        self.__loop:bool = loop                             # Loop the animation (generator)
        self._set_batch_size(batch_size)                    # Set batch size from parameter
        self._player_speed_ms:int = 10                      # Default speed in ms between frames
        main_tag:str = tag if tag else "animation"
        self._task_tag:str = f"{main_tag}.player"
        if animation is not None and not self._set_animation(animation):
            raise Exception("Invalid animation function provided.")
        self.__running:bool = True

    def _set_animation(self, animation:callable) -> bool:
        """
        Setter to change/set current animation.
        """
        if callable(animation):
            self.animation = animation
            return True
        return False

    def _set_batch_size(self, batch_size:int) -> None:
        """
        Setter to change/set batch size.
        - with max batch size check (due to async event loop feeding)
        """
        if batch_size is None:
            return
        self.__batch_size = max(0, min(batch_size, self.__max_batch_size))

    async def _render(self, my_task):
        # Cache methods for speed
        clear = self.clear
        update = self.update
        draw = self.draw
        # Cache the current animation for comparison
        current_animation = self.animation
        frame_counter = 0
        # Clear the display before each frame
        if not self.batch_draw:
            clear()
        for data in self.animation():
            # Check if animation has changed under the loop
            if not self.__running or self.animation != current_animation:
                # Animation changed — break — clean and restart animation loop.
                clear()
                break
            # Update data cache
            update(*data)
            if self.batch_draw:
                # Batched draw mode
                frame_counter += 1
                if frame_counter >= self.__batch_size:
                    draw()
                    frame_counter = 0
                    await my_task.feed(sleep_ms=self._player_speed_ms)
            else:
                # Real-time draw mode
                draw()
                await my_task.feed(sleep_ms=self._player_speed_ms)

    async def _player(self):
        """
        Async task to play the current animation.
        """
        with micro_task(tag=self._task_tag) as my_task:
            while self.__running:
                my_task.out = f"Play {self.animation.__name__} ({self._player_speed_ms}ms/frame)"
                try:
                    await self._render(my_task)
                except IndexError:
                    # Draw after generator exhausted and Restart animation if IndexError occurs
                    self.draw()
                    if not self.__loop:
                        break
                    await my_task.feed(sleep_ms=self._player_speed_ms)
                    my_task.out = "Restart animation"
                except Exception as e:
                    my_task.out = f"Error: {e}"
                    break
            my_task.out = f"Animation stopped...{my_task.out}"

    def control(self, play_speed_ms:int, bt_draw:bool=None, bt_size:int=None, loop:bool=None):
        """
        Set/Get current play speed of the animation.
        :param play_speed_ms: player loop speed in milliseconds.
        :param bt_draw: batch drawing flag.
        :param bt_size: batch drawing size.
        :param loop: loop flag.
        """
        if isinstance(play_speed_ms, int):
            self._player_speed_ms = max(0, min(10000, int(play_speed_ms)))
        if isinstance(bt_draw, bool):
            self.batch_draw = bt_draw
        if isinstance(bt_size, int):
            self._set_batch_size(bt_size)
        if isinstance(loop, bool):
            self.__loop = loop
        return {"realtime": not self.batch_draw, "batched": self.batch_draw,
                "size": self.__batch_size, "speed_ms": self._player_speed_ms,
                "loop": self.__loop}


    def play(self, animation=None, speed_ms=None, bt_draw=False, bt_size=None, loop=True):
        """
        Play animation via generator function.
        :param animation: Animation generator function.
        :param speed_ms: Speed of the animation in milliseconds. (min.: 3ms)
        :param bt_draw: batch drawing flag.
        :param bt_size: batch drawing size.
        :param loop: Loop the animation.
        :return: Player settings.
        """

        if animation is not None:
            if not self._set_animation(animation):
                return "Invalid animation"
        if self.animation is None:
            return "No animation to play"
        # Handle player settings
        settings = self.control(play_speed_ms=speed_ms, bt_draw=bt_draw, bt_size=bt_size,  loop=loop)
        # Ensure async loop set up correctly. (After stop operation, it is needed)
        self.__running = True
        # [!] ASYNC TASK CREATION
        raw_state:bool = micro_task(tag=self._task_tag, task=self._player())
        state = "starting" if raw_state else "running"
        settings["state"] = state
        return settings

    def stop(self):
        """
        Stop the animation.
        """
        self.__running = False
        return "Stop animation player"

    def update(self, *arg, **kwargs):
        """
        Child class must implement this method to handle drawing logic.
        """
        raise NotImplementedError("Child class must implement update method.")

    def draw(self):
        """
        Draw the current frame.
        """
        raise NotImplementedError("Child class must implement draw method.")

    def clear(self):
        """
        Clear the display.
        """
        raise NotImplementedError("Child class must implement clear method.")
