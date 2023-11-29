"""
Module is responsible for user executables invocation
- Wraps LM execution into async tasks
Used in:
- Shell (SocketServer)
- InterruptHandler
- Hooks

Designed by Marcell Ban aka BxNxM
"""

#################################################################
#                           IMPORTS                             #
#################################################################
import uasyncio as asyncio
from micropython import schedule
from sys import modules
from json import dumps
from Debug import console_write, errlog_add
from ConfigHandler import cfgget
from utime import ticks_ms, ticks_diff
from Network import sta_high_avail

try:
    from gc import collect
except:
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
    TASKS = {}                       # TASK OBJ list

    def __init__(self):
        self.task = None             # [TASK] Store created async task object
        self.done = asyncio.Event()  # [TASK] Store done state
        self.out = ""                # [TASK] Store output
        self.tag = None              # [TASK] Task tag (identification)

    @staticmethod
    def is_busy(tag):
        """
        Check task is busy by tag in TASKS
        - exists + running = busy
        """
        task = TaskBase.TASKS.get(tag, None)
        if task is not None and not task.done.is_set():
            # is busy
            return True
        # is NOT busy
        return False

    def cancel(self):
        """
        Cancel task (+cleanup)
        """
        try:
            if self.task is not None:
                try:
                    self.task.cancel()  # Try to cancel task by asyncio
                except Exception as e:
                    if "can't cancel self" != str(e):
                        errlog_add(f"[IRQ limitation] Task cancel error: {e}")
                self.__task_del()
            else:
                return False
        except Exception as e:
            errlog_add(f"[ERR] Task kill error: {e}")
            return False
        return True

    def __task_del(self, keep_cache=False):
        """
        Delete task from TASKS
        """
        self.done.set()
        if self.tag in TaskBase.TASKS.keys():
            if not keep_cache:              # True - In case of destructor
                del TaskBase.TASKS[self.tag]
        collect()                           # GC collect

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
    def __init__(self):
        super().__init__()

    def create(self, callback=None, tag=None):
        """
        Create async task with coroutine callback (no queue limit check!)
        + async socket server task
        + async idle task start
        - other...
        """
        # Create task tag
        self.tag = f"aio{len(TaskBase.TASKS)}" if tag is None else tag
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
        self.done.set()
        collect()           # GC collect


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
        while True:
            await asyncio.sleep_ms(self.__sleep)
            _exec_lm_core(self.__callback, msgobj=lambda msg: setattr(self, 'out', msg.strip()))
            if not self.__inloop:
                break
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
    INSTANCE = None                      # Manager object
    QUEUE_SIZE = cfgget('aioqueue')      # QUEUE size from config
    OLOAD = 0                            # CPU overload measure

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
        return sum([1 for tag, task in TaskBase.TASKS.items() if not task.done.is_set() and '.' in tag])

    @staticmethod
    def _queue_limiter():
        """
        Check task queue limit
        - compare with active running tasks count
        - when queue full raise Exception!!!
        """
        if Manager._queue_len() >= Manager.QUEUE_SIZE:
            msg = f"[aio] Task queue full: {Manager.QUEUE_SIZE}"
            errlog_add(msg)
            raise Exception(msg)

    async def idle_task(self):
        """
        Create IDLE task - fix IRQ task start
        - Try to measure system load - based on idle task latency
        """

        # FREQUENCY OF IDLE TASK - IMPACTS IRQ TASK SCHEDULING, SMALLER IS BEST
        my_task = TaskBase.TASKS.get('idle')
        my_task.out = f"i.d.l.e: 200ms"
        try:
            while True:
                await asyncio.sleep_ms(300)
                # PROBE SYSTEM LOAD
                t = ticks_ms()
                await asyncio.sleep_ms(300)
                # SysLogic block - sys load
                delta_rate = int(((ticks_diff(ticks_ms(), t) / 300)-1) * 100)
                Manager.OLOAD = int((Manager.OLOAD + delta_rate) / 2)       # Average - smooth
                # NETWORK AUTO REPAIR
                if self.idle_counter > 50:       # ~30 sec
                    self.idle_counter = 0        # Reset counter
                    # Check and fix STA network (example: after power outage - micrOS boards boots faster then router)
                    sta_high_avail()
                self.idle_counter += 1           # Increase counter
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
    def list_tasks():
        """
        Primary interface
            List tasks - micrOS top :D
        """
        q = Manager.QUEUE_SIZE - Manager._queue_len()
        output = ["---- micrOS  top ----", f"#queue: {q} #load: {Manager.OLOAD}%\n", "#Active   #taskID"]
        for tag, task in TaskBase.TASKS.items():
            is_running = 'No' if task.done.is_set() else 'Yes'
            spcr = " " * (10 - len(is_running))
            task_view = f"{is_running}{spcr}{tag}"
            output.append(task_view)
        return tuple(output)

    @staticmethod
    def _parse_tag(tag):
        """GET TASK(s) BY TAG - module.func or module.*"""
        task = TaskBase.TASKS.get(tag, None)
        if task is None:
            _tasks = []
            tag_parts = tag.split('.')
            for t in TaskBase.TASKS.keys():
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

def exec_lm_pipe(taskstr):
    """
    Input: taskstr contains LM calls separated by ;
    Used for execute config callback parameters (BootHook, ...)
    """
    try:
        # Handle config default empty value (do nothing)
        if taskstr.startswith('n/a'):
            return True
        # Execute individual commands - msgobj->"/dev/null"
        for cmd in (cmd.strip().split() for cmd in taskstr.split(';') if len(cmd) > 0):
            if not exec_lm_core(cmd):
                console_write(f"|-[LM-PIPE] task error: {cmd}")
    except Exception as e:
        console_write(f"[IRQ-PIPE] error: {taskstr}\n{e}")
        errlog_add(f"[ERR] exec_lm_pipe error: {e}")
        return False
    return True


def exec_lm_pipe_schedule(taskstr):
    """
    Wrapper for exec_lm_pipe
    - Schedule LM executions from IRQs (extIRQ, timIRQ)
    """
    try:
        schedule(exec_lm_pipe, taskstr)
        return True
    except Exception as e:
        errlog_add(f"exec_lm_pipe_schedule error: {e}")
        return False


def exec_lm_core(arg_list, msgobj=None):
    """
    Main LM executor function wrapper
    - handle async (background) task execution
    - handle sync task execution (_exec_lm_core)
    """

    # Handle default msgobj >dev/null
    if msgobj is None:
        msgobj = lambda msg: None

    def task_manager(msg_list):
        msg_len = len(msg_list)
        # [1] Handle task manipulation commands: list, kill, show - return True -> Command handled
        if 'task' == msg_list[0]:
            # task list
            if msg_len > 1 and 'list' == msg_list[1]:
                tasks = '\n'.join(Manager.list_tasks())
                tasks = f'{tasks}\n'
                msgobj(tasks)
                return True
            # task kill <taskID> / task show <taskID>
            if msg_len > 2:
                if 'kill' == msg_list[1]:
                    state, msg = Manager.kill(tag=msg_list[2])
                    msgobj(msg)
                    return True
                if 'show' == msg_list[1]:
                    msgobj(Manager.show(tag=msg_list[2]))
                    return True
            msgobj("Invalid task cmd! Help: task list / kill <taskID> / show <taskID>")
            return True
        # [2] Start async task, postfix: &, &&
        if msg_len > 2 and '&' in arg_list[-1]:
            # Evaluate task mode: loop + delay
            mode = arg_list.pop(-1)
            loop = mode.count('&') == 2
            delay = mode.replace('&', '').strip()
            delay = int(delay) if delay.isdigit() else None
            # Create and start async lm task
            try:
                state = Manager.create_task(arg_list, loop=loop, delay=delay)
            except Exception as e:
                msgobj(e)
                # Valid & handled task command
                return True
            tag = '.'.join(arg_list[0:2])
            if state:
                msgobj(f"Start {tag}")
            else:
                msgobj(f"{tag} is Busy")
            # Valid & handled task command
            return True
        # Not valid task command
        return False
    '''_________________________________________________'''

    # [1] Run task command: start (&), list, kill, show
    if task_manager(arg_list):
        return True
    # [2] Sync "realtime" task execution
    return _exec_lm_core(arg_list, msgobj)


def _exec_lm_core(arg_list, msgobj):
    """
    MAIN FUNCTION TO RUN STRING MODULE.FUNCTION EXECUTIONS
    [1] module name (LM)
    [2] function
    [3...] parameters (separator: space)
    NOTE: msgobj - must be a function with one input param (stdout/file/stream)
    """

    def __conv_func_params(param):
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

    # Dict output user format / jsonify
    def __format_out(json_mode, lm_func, output):
        if isinstance(output, dict):
            # json True: output->json else Format dict output "human readable"
            return dumps(output) if json_mode else '\n'.join([f" {key}: {value}" for key, value in lm_output.items()])
        # Handle output data stream
        if lm_func == 'help':
            # Special case for help command: json True: output->json else Format dict output "human readable"
            return dumps(output) if json_mode else '\n'.join([f" {out}," for out in output])
        return output

    # Check json mode for LM execution
    json_mode = arg_list[-1] == '>json'
    cmd_list = arg_list[0:-1] if json_mode else arg_list
    # LoadModule execution
    if len(cmd_list) >= 2:
        lm_mod, lm_func, lm_params = f"LM_{cmd_list[0]}", cmd_list[1], __conv_func_params(' '.join(cmd_list[2:]))
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
                    errlog_add(f"_exec_lm_core re-import {lm_mod}!")
                    # [2.1] LOAD MODULE - FORCED
                    exec(f"import {lm_mod}")
                    # [2.2] EXECUTE FUNCTION FROM MODULE - over msgobj (socket or stdout)
                    lm_output = eval(f"{lm_mod}.{lm_func}({lm_params})")
                else:
                    raise Exception(e)
            # ---------------------------------------------- #
            # Handle output data stream
            lm_output = __format_out(json_mode, lm_func, lm_output)
            # Return LM exec result via msgobj
            msgobj(str(lm_output))
            return True
            # ------------------------- #
        except Exception as e:
            msgobj(f"exec_lm_core {lm_mod}->{lm_func}: {e}")
            if 'memory allocation failed' in str(e) or 'is not defined' in str(e):
                # UNLOAD MODULE IF MEMORY ERROR HAPPENED
                if lm_mod in modules.keys():
                    del modules[lm_mod]
                # Exec FAIL -> recovery action in SocketServer
                return False
    msgobj("SHELL: type help for single word commands (built-in)")
    msgobj("SHELL: for LM exec: [1](LM)module [2]function [3...]optional params")
    # Exec OK
    return True


def exec_lm_core_schedule(arg_list):
    """
    Wrapper for exec_lm_core for Scheduler
    - micropython scheduling
        - exec protection for cron IRQ
    """
    try:
        schedule(exec_lm_core, arg_list)
        return True
    except Exception as e:
        errlog_add(f"schedule_lm_exec {arg_list} error: {e}")
        return False
