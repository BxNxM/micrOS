import _thread
from utime import sleep


class BgTask:
    singleton_instance = None
    lm_exec_callback = None

    def __init__(self, exec_lm_core=None):
        """
        Singleton design pattern
        __new__ - Customize the instance creation
        self     - class
        """
        # SocketServer singleton properties
        self.__mutex = _thread.allocate_lock()        # Thread mutex - In case of multiple threads and thread monitoring
        self.__exit = _thread.allocate_lock()         # Thread exit mutex
        self.__main_mutex = _thread.allocate_lock()   # Main mutex - interrupt thread
        self.__loop = False
        self.__ret = ''
        self.__taskid = (0, 'none')
        self.main_lm = None
        if exec_lm_core is not None:
            BgTask.lm_exec_callback = exec_lm_core

    @staticmethod
    def singleton(exec_lm_core=None, main_lm=None):
        # Instantiate BgTask if not exists
        if BgTask.singleton_instance is None:
            BgTask.singleton_instance = BgTask()
        # Store requested main load module for collision check
        BgTask.singleton_instance.main_lm = main_lm if isinstance(main_lm, str) else None
        # Store lm executor callback
        if exec_lm_core is not None:
            BgTask.lm_exec_callback = exec_lm_core
        return BgTask.singleton_instance

    def __enter__(self):
        """
        Allocate thread lock from main
        - protect execution scope
        - if self.main_lm is None - block by default
        """
        # Module Collision Check
        #  thread execution is active: self.__exit True + matching LoadModule
        if self.__exit.locked() and (self.main_lm is None or self.main_lm == self.__taskid[1].split('.')[0]):
            self.__main_mutex.acquire()
            self.__mutex.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Release thread lock from main
        - if self.main_lm is None - block by default
        """
        # Release main lock on thread if it was locked and matching LoadModule
        if self.__main_mutex.locked() and (self.main_lm is None or self.main_lm == self.__taskid[1].split('.')[0]):
            self.__main_mutex.release()
            self.__mutex.release()

    def __th_task(self, arglist, delay):
        """
        Worker thread wrapper
        :param arglist: Load module + function + params
        :param delay: Thread delay in sec
        """
        self.__exit.acquire()
        while True:
            # Set delay
            sleep(delay)

            # SKIP thread until main exec running
            if self.__main_mutex.locked():
                continue

            # Set worker lock
            self.__mutex.acquire()
            # RUN CALLBACK
            call_return = BgTask.lm_exec_callback(arglist, msgobj=self.msg)
            self.__ret = '{} [{}]'.format(self.__ret, call_return)
            self.__mutex.release()
            # Exit thread
            if not self.__loop:
                break
        self.__exit.release()

    def msg(self, msg):
        self.__ret += msg
        if len(self.__ret) > 80:
            self.__ret = self.__ret[-80:]

    def run(self, arglist, loop=None, delay=0):
        # Return if busy - single user job support
        if self.__exit.locked():
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
        if self.__exit.locked() or self.__loop:
            self.__loop = False
            return '[BgJob] Stop {}'.format(self.__taskid)
        return '[BgJob] Already stopped {}'.format(self.__taskid)

    def info(self):
        return {'isbusy': self.__exit.locked(), 'taskid': self.__taskid, 'out': self.__ret}


"""
################################ TEST CODE ################################

import random
import time

TEST_LOOP = 30          # Test (main) loop iteration

WORKER_WAIT_MAX = 10    # ms
MAIN_WAIT_MAX = 10      # ms
IDLE_WAIT_MAX = 50      # ms


class TestData:
    THREAD_CALL = 0
    MAIN_CALL = 0
    MAIN_EXEC_T = 0
    THREAD_EXEC_T = 0
    MAIN_IDLE_T = 0

    @staticmethod
    def stat():
        out = "MAIN/THREAD CALL: {} %\n".format(round((TestData.MAIN_CALL/TestData.THREAD_CALL)*100))
        out += "MAIN T: {} s ({})\n".format(round((TestData.MAIN_EXEC_T/TestData.MAIN_CALL), 4), TestData.MAIN_EXEC_T)
        out += "THREAD T: {} s ({})\n".format(round(TestData.THREAD_EXEC_T/TestData.THREAD_CALL, 4), TestData.THREAD_EXEC_T)
        out += "MAIN/THREAD CALL: {}/{}".format(TestData.MAIN_CALL, TestData.THREAD_CALL)
        return out

    @staticmethod
    def clean():
        TestData.THREAD_CALL = 0
        TestData.MAIN_CALL = 0
        TestData.MAIN_EXEC_T = 0
        TestData.THREAD_EXEC_T = 0
        TestData.MAIN_IDLE_T = 0


def test_worker(arglist, msgobj=None):
    TestData.THREAD_CALL += 1
    start = time.time()
    with open('thread_main_test.dat', 'a+') as f:
        datastr = ' '.join(arglist)
        f.write('{}\n'.format(datastr))
    print('\t\t!!! {}'.format(arglist))
    if msgobj is not None:
        msgobj(str(arglist))
    sleep(random.randint(0, WORKER_WAIT_MAX)/100)
    TestData.THREAD_EXEC_T += time.time() - start


def test_executor(info, worker_tag, conflict=False, force=False, loop=False):
    # Store title in file
    with open('thread_main_test.dat', 'a+') as f:
        f.write(f'{info}\n')

    # Module parameters
    module = 'BgJob'
    # Modify module for testing
    if conflict:
        main_module = module
    else:
        main_module = 'NEW'
    if force:
        main_module = None

    # Initiate background job
    job = BgTask.singleton(exec_lm_core=test_worker)

    # Start background job
    success = False
    while not success:
        out = job.run(arglist=[module, worker_tag], loop=loop)
        print(out)
        success = out[0]

    # Run main thread
    for _ in range(TEST_LOOP):
        TestData.MAIN_CALL += 1
        start = time.time()
        with BgTask.singleton(main_lm=main_module):
            test_worker(['\tMAIN', '\t- START'])
            sleep(random.randint(0, MAIN_WAIT_MAX)/100)
            test_worker(['\tMAIN', '\t- STOP'])
        TestData.MAIN_EXEC_T += time.time() - start
        # IDLE
        start = time.time()
        sleep(random.randint(0, IDLE_WAIT_MAX) / 100)
        TestData.MAIN_IDLE_T += time.time() - start

    # Stop job
    job.stop()
    # Store test result
    out = TestData.stat()
    print(out)
    with open('thread_main_test.dat', 'a+') as f:
        f.write("------- SUM ------\n")
        f.write(out+'\n\n')
    # Cleanup
    TestData.clean()


# 1
def test_conflicting_module_loop():
    info = '\nConflicting module test in loop...'
    worker_tag = 'THREAD_CF_LOOP'
    test_executor(info, worker_tag, conflict=True, force=False, loop=True)


# 2
def test_not_conflicting_module_loop():
    info = '\nNOT Conflicting module test in loop...'
    worker_tag = 'THREAD_NCF_LOOP'
    test_executor(info, worker_tag, conflict=False, force=False, loop=True)


# 3
def test_conflicting_module_single():
    info = '\nConflicting module test single...'
    worker_tag = 'THREAD_SIMPLE'
    test_executor(info, worker_tag, conflict=True, force=False, loop=False)


# 4
def test_not_conflicting_module_loop_force():
    info = '\nNOT Conflicting module test in loop FORCE LOCK...'
    worker_tag = 'THREAD_FORCE_LOOP'
    test_executor(info, worker_tag, conflict=False, force=True, loop=True)


if __name__ == "__main__":
    with open('thread_main_test.dat', 'w') as ff:
        ff.write(f'THREAD TEST\n')

    test_conflicting_module_loop()
    time.sleep(1)
    test_not_conflicting_module_loop()
    time.sleep(1)
    test_conflicting_module_single()
    time.sleep(1)
    test_not_conflicting_module_loop_force()
"""
