import _thread
from time import sleep
from LmExecCore import exec_lm_core


class BgTask:
    __instance = None

    def __new__(cls, delay=1, loop=False):
        """
        Singleton design pattern
        __new__ - Customize the instance creation
        cls     - class
        """
        if cls.__instance is None:
            # SocketServer singleton properties
            cls.__instance = super().__new__(cls)
            cls.__lock = _thread.allocate_lock()
            cls.__loop = loop
            cls.__isbusy = False
            cls.__ret = ''
            cls.__taskid = (0, 'none')
        return cls.__instance

    def __enter__(cls):
        if cls.__lock.locked():
            return
        cls.__lock.acquire()

    def __exit__(cls, exc_type, exc_val, exc_tb):
        if cls.__lock.locked():
            cls.__lock.release()

    def __th_task(cls, arglist, delay=1):
        cls.__isbusy = True
        while True:
            # Set delay
            sleep(delay) if delay > 0 else sleep(0.1)
            # Check thread lock - wait until release
            if cls.__lock.locked():
                continue
            # RUN CALLBACK
            call_return = exec_lm_core(arglist, msgobj=cls.msg)
            cls.__ret = '{} [{}]'.format(cls.__ret, call_return)
            # Exit thread
            if not cls.__loop:
                break
        cls.__isbusy = False

    def msg(cls, msg):
        cls.__ret += msg
        if len(cls.__ret) > 80:
            cls.__ret = cls.__ret[-80:]

    def run(cls, arglist, loop=None, delay=None):
        # Return if busy - single job support
        if cls.__isbusy:
            return False, cls.__taskid
        # Set thread params
        cls.__ret = ''
        id_num = 0 if cls.__taskid[0] > 19 else cls.__taskid[0]+1
        cls.__taskid = (id_num, '{}.{}'.format(arglist[0], arglist[1]))
        cls.__loop = cls.__loop if loop is None else loop
        # Start thread
        _thread.start_new_thread(cls.__th_task, (arglist, delay))
        return True, cls.__taskid

    def stop(cls):
        if cls.__isbusy or cls.__loop:
            cls.__loop = False
            return '[BgJob] Stop {}'.format(cls.__taskid)
        return '[BgJob] Already stopped {}'.format(cls.__taskid)

    def info(cls):
        return {'isbusy': cls.__isbusy, 'taskid': cls.__taskid, 'out': cls.__ret}

