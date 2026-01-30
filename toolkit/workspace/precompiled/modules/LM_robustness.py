from LM_system import memory_usage
from Common import socket_stream, syslog, micro_task
from Auth import sudo


@socket_stream
def raise_error(msgobj=None):
    """
    Test function - raise  LM exception
    """
    if msgobj is not None:
        msgobj("Raise test exception")
    state = syslog('Robustness TeSt ErRoR')
    raise Exception(f"Test exception: {'OK' if state else 'NOK'}")


@socket_stream
def memory_leak(cnt=160, msgobj=None):
    """
    Test function - allocate lot of memory
    :param cnt: data counter, default 160 iteration
    :return: verdict
    """
    dict_test = {}
    mem_start = memory_usage()['mem_used']
    for k in range(cnt):
        mem = memory_usage()['percent']
        data = "micrOS memory usage: {} %".format(mem)
        if msgobj is not None:
            msgobj("[{}] gen: {}".format(k, data))
        dict_test[k] = data
    mem_end = memory_usage()['mem_used']
    delta = mem_start - mem_end
    return '[{}] RAM Alloc.: {} kB {} byte'.format(len(dict_test), int(delta / 1024), int(delta % 1024))

@socket_stream
def recursion_limit(limit=14, msgobj=None):
    cnt = 0
    for cnt in range(1, limit+1):
        try:
            _recursion(cnt, msgobj=msgobj)
        except Exception as e:
            msgobj(f"ok error: {e}")
            break
    return f"Recursion limit: {cnt}"


def _recursion(cnt, msgobj=None):
    """
    Test function - recursion test
    :param cnt: recursion depth
    :return: verdict
    Error example:
        node01 $  robustness recursion_limit 15
        lm_exec LM_robustness->recursion_limit: maximum recursion depth exceeded
    """
    if cnt > 0:
        remain = _recursion(cnt-1)
        if msgobj is not None:
            msgobj("recalled {}".format(cnt))
    else:
        remain = 0
    return remain

################## TEST micro_task UCs ##########################

async def __task(tag, period_ms):
    counter = 0
    with micro_task(tag=tag) as my_task:
        while True:
            # DO something here in the async loop...
            counter += 1

            # Store data in task cache (task show mytask)
            my_task.out = f'MyTask Counter: {counter}'

            # Async sleep - feed event loop
            await my_task.feed(sleep_ms=period_ms)
            # [i] feed same as "await asyncio.sleep_ms(period_ms)" with micrOS features (WDT)

def create_task():
    """
    Legacy way of task creation (with exact task tagging)
    """
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    task_tag = "microtask.run"
    return micro_task(tag=task_tag, task=__task(tag=task_tag, period_ms=5))


@micro_task("microtask", _wrap=True)
async def mytask(tag, period_ms=30):
    """
    New shorter way of task creation
     with decorator function
    """
    counter = 0
    with micro_task(tag=tag) as my_task:
        while True:
            # DO something here in the async loop...
            counter += 1

            # Store data in task cache (task show mytask)
            my_task.out = f'MyTask Counter: {counter}'

            # Async sleep - feed event loop
            await my_task.feed(sleep_ms=period_ms)
            # [i] feed same as "await asyncio.sleep_ms(period_ms)" with micrOS features (WDT)


@sudo
def func_sudo():
    """
    Function execution requires pwd=<...>
    """
    return "Access granted"


@sudo(_force_only=(True, 0))
def func_sudo_force(force=False):
    """
    Function requires pwd=<...> when force=True
    """
    return f"Access granted, force flag: {force}"

##############################################################################

def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'NOTE: This is a test module to validate system robustness', \
           'raise_error', 'memory_leak cnt=160', 'recursion_limit cnt=14', \
           'create_task', 'mytask', "func_sudo", "func_sudo_force"

