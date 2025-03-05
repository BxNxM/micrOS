"""
Module is responsible for user executables invocation
- Wraps LM execution into async tasks

Designed by Marcell Ban aka BxNxM
"""

#################################################################
#                           IMPORTS                             #
#################################################################
from sys import modules
from json import dumps
import uasyncio as asyncio
from micropython import schedule
from utime import ticks_ms, ticks_diff
from Debug import console_write, errlog_add
from Config import cfgget
from Network import sta_high_avail

try:
    from gc import collect
except ImportError:
    console_write("[SIMULATOR MODE GC IMPORT]")
    from simgc import collect

#################################################################
#                Implement custom task class                    #
#              TaskBase, NativeTask, MagicTask                  #
#################################################################


class TaskBase:
    """
    Async task base definition for common features
    """
    __slots__ = ['task', 'done', 'out', 'tag', '__callback', '__inloop', '__sleep']
    QUEUE_SIZE = cfgget('aioqueue')     # QUEUE size from config
    TASKS = {}                          # TASK OBJ list

    def __init__(self):
        self.task = None             # Store created async task object
        self.tag = None              # Task tag (identification)
        self.done = asyncio.Event()  # Store task done state
        self.out = ""                # Store task output

    @staticmethod
    def is_busy(tag) -> bool:
        """
        Check task is busy by tag
        :param tag: for task selection
        """
        task = TaskBase.TASKS.get(tag, None)
        # return True: busy OR False: not busy (inactive)
        return bool(task is not None and not task.done.is_set())

    @staticmethod
    def task_gc():
        """
        Automatic passive task deletion over QUEUE_SIZE
        """
        keep  = TaskBase.QUEUE_SIZE
        passive = tuple((task_tag for task_tag in list(TaskBase.TASKS) if not TaskBase.is_busy(task_tag)))
        if len(passive) >= keep:
            for i in range(0, len(passive)-keep+1):
                del TaskBase.TASKS[passive[i]]
            collect()  # GC collect

    def cancel(self) -> bool:
        """
        Cancel task (+cleanup)
        """
        try:
            if self.task is not None:
                try:
                    self.task.cancel()  # Try to cancel task by asyncio
                except Exception as e:
                    if "can't cancel self" != str(e):
                        errlog_add(f"[WARN] IRQ Task cancel: {e}")
                self.__task_del()
            else:
                return False
        except Exception as e:
            errlog_add(f"[ERR] Task kill: {e}")
            return False
        return True

    def __task_del(self, keep_cache=False):
        """
        Delete task from TASKS
        """
        self.done.set()
        if self.tag in TaskBase.TASKS:
            if not keep_cache:              # True - In case of destructor
                del TaskBase.TASKS[self.tag]
        collect()                           # GC collect

    @staticmethod
    async def feed(sleep_ms=1):
        """
        Feed event loop
        :param sleep_ms: in millisecond (min: 1)
        """
        # TODO: feed WDT - preemptive cooperative multitasking aka reboot if no feed until X time period
        return await asyncio.sleep_ms(sleep_ms)

    def __del__(self):
        try:
            self.__task_del(keep_cache=True)
        except Exception as e:
            errlog_add(f"[ERR] TaskBase.__del__: {e}")


class NativeTask(TaskBase):
    """
    Run native async task from code
    - could be built in function or custom code from load modules
    """

    def create(self, callback=None, tag=None):
        """
        Create async task with coroutine callback (no queue limit check!)
        + async socket server task
        + async idle task starts
        - other...
        """
        # Create task tag
        self.tag = f"aio.{ticks_ms()}" if tag is None else tag
        if TaskBase.is_busy(self.tag):
            # Skip task if already running
            return False

        # Start task with coroutine callback
        self.task = asyncio.get_event_loop().create_task(callback)
        # Store Task object by key - for task control
        TaskBase.TASKS[self.tag] = self
        return True

    def __enter__(self):
        """
        START CONDITION
        Helper function for Task creation in Load Modules
        [HINT] Use python with feature to utilize this feature
        """
        self.done.clear()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        AUTOMATIC STOP CONDITION
        Helper function for Task creation in Load Modules
        [HINT] Use python with feature to utilize this feature
        """
        self.task_gc()    # Task pool cleanup
        self.done.set()


class MagicTask(TaskBase):
    """
    Run LoadModule calls as async function
    - wrap sync code into async context
    """

    def __init__(self):
        super().__init__()
        self.__callback = None       # [LM] Task callback: list of strings (LM call)
        self.__inloop = False        # [LM] Task while loop for LM callback
        self.__sleep = 20            # [LM] Task while loop - async wait (proc feed) [ms]

    def create(self, callback=None, loop=None, sleep=None):
        """
        Create async task with function callback (with queue limit check)
        - wrap (sync) function into async task (task_wrapper)
        - callback: <load_module> <function> <param> <param2>
        - loop: bool
        - sleep: [ms]
        """
        # Create task tag
        self.tag = '.'.join(callback[0:2])
        if TaskBase.is_busy(self.tag):
            # Skip task if already running
            return False

        # Set parameters for async wrapper
        self.__callback = callback
        self.__inloop = self.__inloop if loop is None else loop
        # Set sleep value for async loop - optional parameter with min sleep limit check (20ms)
        self.__sleep = self.__sleep if sleep is None else sleep if sleep > 19 else self.__sleep

        self.task = asyncio.get_event_loop().create_task(self.__task_wrapper())
        # Store Task object by key - for task control
        TaskBase.TASKS[self.tag] = self
        return True

    async def __task_wrapper(self):
        """
        Implements async wrapper around Load Module call
        - self.__callback: list - contains LM command strings
        - self.__sleep: main event loop feed
        - self.__inloop: lm call type - one-shot (False) / looped (True)
        - self.__msg_buf: lm msg object redirect to variable - store lm output
        """
        jsonify = self.__callback[-1] == '>json'
        if jsonify:
            self.__callback = self.__callback[:-1]
        while True:
            await self.feed(self.__sleep)
            state, self.out = _exec_lm_core(self.__callback, jsonify)
            if not state or not self.__inloop:
                break
        self.task_gc()    # Task pool cleanup
        self.done.set()

    def cancel(self):
        self.__inloop = False  # Set soft stop (LM task)
        return super().cancel()


#################################################################
#                 Implement Task manager class                  #
#################################################################


class Manager:
    """
    micrOS async task handler
    """
    __slots__ = ['_initialized', 'idle_counter']
    INSTANCE = None                      # Manager object
    LOAD = 0                             # CPU overload measure

    def __new__(cls):
        """
        Singleton design pattern
        __new__ - Customize the instance creation
        cls     - class
        """
        if not Manager.INSTANCE:
            # TaskManager singleton properties
            cls.INSTANCE = super(Manager, cls).__new__(cls)
            cls.INSTANCE._initialized = False
            # Set async event loop exception handler
            asyncio.get_event_loop().set_exception_handler(lambda loop=None, context=None:
                                                           errlog_add(f"[aio] exception: {loop}:{context}"))
        return cls.INSTANCE

    def __init__(self):
        if not self._initialized:
            # Start system idle task (IRQ(hack) + monitoring)
            self.idle_counter = 0  # For idle task rare action scheduling
            self.create_task(callback=self.idle_task(), tag="idle")
            self._initialized = True
            console_write("[TASK MANAGER] <<constructor>>")

    @staticmethod
    def _queue_len():
        # Get active Load Module tasks (tag: module.function)
        return sum((1 for tag, task in TaskBase.TASKS.items() if not task.done.is_set() and '.' in tag))

    @staticmethod
    def _queue_limiter():
        """
        Check task queue limit
        - compare with active running tasks count
        - when queue full raise Exception!!!
        """
        if Manager._queue_len() >= TaskBase.QUEUE_SIZE:
            msg = f"[aio] Task queue full: {TaskBase.QUEUE_SIZE}"
            errlog_add(msg)
            raise Exception(msg)

    async def idle_task(self):
        """
        Create IDLE task - fix IRQ task start
        - Try to measure system load - based on idle task latency
        """

        # FREQUENCY OF IDLE TASK - IMPACTS IRQ TASK SCHEDULING, SMALLER IS BEST
        my_task = TaskBase.TASKS.get('idle')
        my_task.out = "i.d.l.e: 600ms"
        try:
            while True:
                # [0] Just chill
                await my_task.feed(300)
                # [1] PROBE SYSTEM LOAD + 300ms
                t = ticks_ms()
                await my_task.feed(300)
                delta_rate = int(((ticks_diff(ticks_ms(), t) / 300) - 1) * 100)
                Manager.LOAD = int((Manager.LOAD + delta_rate) / 2)  # Average - smooth
                # [2] NETWORK AUTO REPAIR
                if self.idle_counter > 200:  # ~120 sec
                    self.idle_counter = 0    # Reset counter
                    # Check and fix STA network (example: after power outage - micrOS boards boots faster then router)
                    sta_high_avail()
                self.idle_counter += 1  # Increase counter
        except Exception as e:
            errlog_add(f"[ERR] Idle task exists: {e}")
        my_task.done.set()

    @staticmethod
    def create_task(callback, tag=None, loop=False, delay=None):
        """
        Primary interface
        Generic task creator method
            Create async Task with coroutine/list(lm call) callback
        """
        if isinstance(callback, list):
            # Check queue if task is Load Module
            Manager._queue_limiter()
            return MagicTask().create(callback=callback, loop=loop, sleep=delay)
        # No limit for Native tasks!!!
        return NativeTask().create(callback=callback, tag=tag)

    @staticmethod
    def list_tasks(json=False):
        """
        Primary interface
            List tasks - micrOS top :D
        """
        q = TaskBase.QUEUE_SIZE - Manager._queue_len()
        out_active = ["---- micrOS  top ----", f"#queue: {q} #load: {Manager.LOAD}%\n", "#Active   #taskID"]
        out_passive = []
        for tag, task in TaskBase.TASKS.items():
            if json:
                view = tag
            else:
                is_running = 'No' if task.done.is_set() else 'Yes'
                spcr = " " * (10 - len(is_running))
                view = f"{is_running}{spcr}{tag}"
            _ = out_passive.append(view) if task.done.is_set() else out_active.append(view)
        return tuple(out_active), tuple(out_passive)

    @staticmethod
    def _parse_tag(tag):
        """GET TASK(s) BY TAG - module.func or module.*"""
        task = TaskBase.TASKS.get(tag, None)
        if task is None:
            _tasks = []
            tag_parts = tag.split('.')
            for t in TaskBase.TASKS:
                if t.startswith(tag_parts[0]) and len(tag_parts) > 1 and tag_parts[1] == '*':
                    _tasks.append(t)
            if len(_tasks) == 0:
                return []
            return _tasks
        return [tag]

    @staticmethod
    def show(tag):
        """
        Primary interface
            Show buffered task output
        """
        tasks = Manager._parse_tag(tag)
        if len(tasks) == 0:
            return f"No task found: {tag}"
        if len(tasks) == 1:
            return TaskBase.TASKS[tasks[0]].out
        output = []
        for t in tasks:
            output.append(f"{t}: {TaskBase.TASKS[t].out}")
        return '\n'.join(output)

    @staticmethod
    def kill(tag):
        """
        Primary interface
        Kill/terminate async task
        - by tag: module.function
        - by tag module.*, kill all for selected module
        """
        def terminate(_tag):
            to_kill = TaskBase.TASKS.get(_tag, None)
            try:
                return False if to_kill is None else to_kill.cancel()
            except Exception as e:
                errlog_add(f"[ERR] Task kill: {e}")
                return False

        # Handle task group kill (module.*)
        tasks = Manager._parse_tag(tag)
        state = True
        if len(tasks) == 0:
            return state, f"No task found: {tag}"
        if len(tasks) == 1:
            msg = f"Kill: {tasks[0]}|{state}"
            return terminate(tasks[0]), msg
        output = []
        for k in tasks:
            state &= terminate(k)
            output.append(f"{k}|{state}")
        msg = f"Kill: {', '.join(output)}"
        return state, msg

    @staticmethod
    def run_forever():
        """
        Run async event loop
        """
        try:
            asyncio.get_event_loop().run_forever()
        except Exception as e:
            errlog_add(f"[aio] loop stopped: {e}")
            asyncio.get_event_loop().close()

    @staticmethod
    def server_task_msg(msg):
        server_task = TaskBase.TASKS.get('server', None)
        if server_task is None:
            return
        server_task.out = msg


#################################################################
#                      LM EXEC CORE functions                   #
#################################################################
def exec_builtins(func):
    """
    [Decorator] Module execution built-in commands and modifiers
    - modules         - show active modules list
    - task kill ...   - task termination
           show ...   - task output dump
    -  ... >json      - postfix to "jsonize" the output
    """
    def wrapper(arg_list, jsonify=None):
        # Ensure the parameter is a list of strings
        if isinstance(arg_list, list) and arg_list:
            # JSONIFY: [1] >json in arg_list or [2] jsonify True/False
            json_flag = arg_list[-1] == '>json'
            if json_flag:
                arg_list = arg_list[:-1]
            json_flag = jsonify if isinstance(jsonify, bool) else json_flag
            # MODULES
            if arg_list[0] == 'modules':
                return True, list((m.strip().replace('LM_', '') for m in modules if m.startswith('LM_'))) + ['task']
            # Handle task manipulation commands: list, kill, show - return True -> Command handled
            if 'task' == arg_list[0]:
                arg_len = len(arg_list)
                # task list
                if arg_len > 1 and 'list' == arg_list[1]:
                    on, off = Manager.list_tasks(json=json_flag)
                    # RETURN:    JSON mode                                                   Human readable mode with cpu & queue info
                    return (True, {'active': on[3:], 'inactive': off}) if json_flag else (True, '\n'.join(on) + '\n' + '\n'.join(off) + '\n')
                # task kill <taskID> / task show <taskID>
                if arg_len > 2:
                    if 'kill' == arg_list[1]:
                        state, msg = Manager.kill(tag=arg_list[2])
                        return True, msg
                    if 'show' == arg_list[1]:
                        return True, Manager.show(tag=arg_list[2])
                return True, "Invalid task cmd! Help: task list / kill <taskID> / show <taskID>"
            # Call the decorated function with the additional flag
            return func(arg_list, json_flag)
    return wrapper


@exec_builtins
def lm_exec(arg_list, jsonify):
    """
    Main LM executor function with
    - async (background)
    - sync
    (single) task execution (_exec_lm_core)
    :param arg_list: command parameters
    :param jsonify: request json output (controlled by the decorator)
    Return Bool(OK/NOK), "Command output"
    """

    # [1] Async "background" task execution, postfix: &, &&
    if len(arg_list) > 2 and '&' in arg_list[-1]:
        # Evaluate task mode: loop + delay
        mode = arg_list.pop(-1)
        loop = mode.count('&') == 2
        delay = mode.replace('&', '').strip()
        delay = int(delay) if delay.isdigit() else None
        # Create and start async lm task
        try:
            state = Manager.create_task(arg_list, loop=loop, delay=delay)
        except Exception as e:
            # Valid & handled task command
            return True, str(e)
        tag = '.'.join(arg_list[0:2])
        # Valid & handled task command
        if state:
            return True, f"Start {tag}"
        return True, f"{tag} is Busy"

    # [2] Sync "realtime" task execution
    state, out = _exec_lm_core(arg_list, jsonify)
    return state, out


def _exec_lm_core(cmd_list, jsonify):
    """
    [CORE] Single command executor: MODULE.FUNCTION...
    :param cmd_list: list of string parameters
        [1] module name (LM)
        [2] function
        [3...] parameters (separator: space)
    :param jsonify: request json output
    Return Bool(OK/NOK), STR(Command output)
    """

    def _func_params(param):
        buf = None
        if "'" in param or '"' in param:
            str_index = [i for i, c in enumerate(param) if c in ('"', "'")]
            buf = [param[str_index[str_i]:str_index[str_i + 1] + 1] for str_i in range(0, len(str_index), 2)]
            for substr in buf:
                param = param.replace(substr, '{}')
        param = param.replace(' ', ', ')
        if isinstance(buf, list):
            param = param.format(*buf)
        return param

    # LoadModule execution
    if len(cmd_list) >= 2:
        lm_mod, lm_func, lm_params = f"LM_{cmd_list[0]}", cmd_list[1], _func_params(' '.join(cmd_list[2:]))
        try:
            # ------------- LM LOAD & EXECUTE ------------- #
            # [1] LOAD MODULE - OPTIMIZED by sys.modules
            if lm_mod not in modules:
                exec(f"import {lm_mod}")
            try:
                # [2] EXECUTE FUNCTION FROM MODULE - over msgobj (socket or stdout)
                lm_output = eval(f"{lm_mod}.{lm_func}({lm_params})")
            except Exception as e:
                # Handle not proper module load (simulator), note: module in sys.modules BUT not available
                if lm_mod in str(e):
                    # [2.1] LOAD MODULE - FORCED
                    exec(f"import {lm_mod}")
                    # [2.2] EXECUTE FUNCTION FROM MODULE - over msgobj (socket or stdout)
                    lm_output = eval(f"{lm_mod}.{lm_func}({lm_params})")
                else:
                    raise e
            # ------------ LM output format: dict(jsonify) / str(raw) ------------- #
            # Handle LM output data
            if isinstance(lm_output, dict):
                # json True: output->json else Format dict output "human readable"
                lm_output = dumps(lm_output) if jsonify else '\n'.join(
                    [f" {key}: {value}" for key, value in lm_output.items()])
            if lm_func == 'help':
                # Special case for help command: json True: output->json else Format dict output "human readable"
                lm_output = dumps(lm_output) if jsonify else '\n'.join([f" {out}," for out in lm_output])
            # Return LM exec result
            return True, str(lm_output)
            # ---------------------------------------------------------------------- #
        except Exception as e:
            if 'memory allocation failed' in str(e) or 'is not defined' in str(e):
                # UNLOAD MODULE IF MEMORY ERROR HAPPENED + gc.collect
                if lm_mod in modules:
                    del modules[lm_mod]
                collect()
            # LM EXECUTION ERROR
            return False, f"Core error: {lm_mod}->{lm_func}: {e}"
    return False, "Shell: for hints type help.\nShell: for LM exec: [1](LM)module [2]function [3...]optional params"


def lm_is_loaded(lm_name):
    """
    [Auth mode]
    Check lm_name in enabled modules
    """
    static_keywords = ('task', 'modules')
    loaded_mods = [lm.replace('LM_', '') for lm in modules if lm.startswith('LM_')]
    return lm_name in static_keywords or lm_name in loaded_mods


#####################  LM EXEC CORE WRAPPERS  #####################

def exec_lm_pipe(taskstr):
    """
    Real-time multi command executor
    - with #comment annotation feature
    :param taskstr: contains LM calls separated by ;
    Used for execute config callback parameters (BootHook, IRQs, ...)
    """
    try:
        # Handle config default empty value (do nothing)
        if taskstr.startswith('n/a'):
            return True
        # Execute individual commands - msgobj->"/dev/null"
        for cmd in (cmd.strip().split() for cmd in taskstr.split(';') if len(cmd) > 0):
            if len(cmd) > 0 and cmd[0].startswith("#"):
                console_write(f"[SKIP] exec_lm_pipe: {' '.join(cmd)}")
                return True
            if not lm_exec(cmd)[0]:
                errlog_add(f"[WARN] exec_lm_pipe: {cmd}")
    except Exception as e:
        errlog_add(f"[ERR] exec_lm_pipe {taskstr}: {e}")
        return False
    return True


def exec_lm_pipe_schedule(taskstr):
    """
    Scheduled Wrapper for exec_lm_pipe for IRQs (extIRQ, timIRQ,  cronIRQ)
    """
    try:
        schedule(exec_lm_pipe, taskstr)
        return True
    except Exception as e:
        errlog_add(f"[ERR] exec_lm_pipe_schedule: {e}")
        return False
