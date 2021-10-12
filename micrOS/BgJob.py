import _thread
from time import sleep


class BgTask:
    singleton_instance = None
    lm_exec_callback = None

    def __init__(self, exec_lm_core=None, loop=False):
        """
        Singleton design pattern
        __new__ - Customize the instance creation
        self     - class
        """
        # SocketServer singleton properties
        self.__lock = _thread.allocate_lock()
        self.__loop = loop
        self.__isbusy = False
        self.__ret = ''
        self.__taskid = (0, 'none')
        if exec_lm_core is not None:
            BgTask.lm_exec_callback = exec_lm_core

    @staticmethod
    def singleton(exec_lm_core=None, loop=False):
        if BgTask.singleton_instance is None:
            BgTask.singleton_instance = BgTask(loop)
        if exec_lm_core is not None:
            BgTask.lm_exec_callback = exec_lm_core
        return BgTask.singleton_instance

    def __enter__(self):
        if self.__lock.locked():
            return
        self.__lock.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__lock.locked():
            self.__lock.release()

    def __th_task(self, arglist, delay=1):
        self.__isbusy = True
        while True:
            # Set delay
            sleep(delay) if delay > 0 else sleep(0.1)
            # Check thread lock - wait until release
            if self.__lock.locked():
                continue
            # RUN CALLBACK
            call_return = BgTask.lm_exec_callback(arglist, msgobj=self.msg)
            self.__ret = '{} [{}]'.format(self.__ret, call_return)
            # Exit thread
            if not self.__loop:
                break
        self.__isbusy = False

    def msg(self, msg):
        self.__ret += msg
        if len(self.__ret) > 80:
            self.__ret = self.__ret[-80:]

    def run(self, arglist, loop=None, delay=None):
        # Return if busy - single job support
        if self.__isbusy:
            return False, self.__taskid
        # Set thread params
        self.__ret = ''
        id_num = 0 if self.__taskid[0] > 19 else self.__taskid[0]+1
        self.__taskid = (id_num, '{}.{}'.format(arglist[0], arglist[1]))
        self.__loop = self.__loop if loop is None else loop
        # Start thread
        _thread.start_new_thread(self.__th_task, (arglist, delay))
        return True, self.__taskid

    def stop(self):
        if self.__isbusy or self.__loop:
            self.__loop = False
            return '[BgJob] Stop {}'.format(self.__taskid)
        return '[BgJob] Already stopped {}'.format(self.__taskid)

    def info(self):
        return {'isbusy': self.__isbusy, 'taskid': self.__taskid, 'out': self.__ret}

