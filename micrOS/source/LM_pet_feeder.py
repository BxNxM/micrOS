from LM_servo import sduty, deinit, pinmap as servo_pinmap
from LM_stepper import step, pinmap as stepper_pinmap
from Common import micro_task


class Data:
    TASK_TAG = "pet_feeder.portion"


async def __portion_task(portion, posmin, posmax):
    # ASYNC TASK ADAPTER [*2] with automatic state management
    #   [micro_task->Task] TaskManager access to task internals (out, done attributes)
    with micro_task(tag=Data.TASK_TAG) as my_task:
        for p in range(0, portion):
            # [1]Run pos fill up
            for pos in range(posmin, posmax):
                sduty(pos)
                await my_task.feed(sleep_ms=15)
            # [2]Wait between fill up / food out
            await my_task.feed(sleep_ms=500)
            # [3]Run pos food out
            for pos in range(posmax, posmin, -1):
                sduty(pos)
                await my_task.feed(sleep_ms=20)
            my_task.out = "{}/{} serving".format(p+1, portion)
    deinit()
    my_task.out += ": {} task done".format(Data.TASK_TAG)


def serve(portion=1, posmin=65, posmax=97):
    """
    Pet feeder - with servo motor
    :param portion: number of portions (min/max positions to repeat)
    :param posmin: servo "start" position
    :param posmax: servo "stop" position
    """
    # [!] ASYNC TASK CREATION [1*] with async task callback + taskID (TAG) handling
    state = micro_task(tag=Data.TASK_TAG, task=__portion_task(portion=portion, posmin=posmin, posmax=posmax))
    return "Starting" if state else "Already running"


def serve_w_stepper(portion=1, forward=135, back=10):
    """
    Pet feeder (beta) - with stepper motor
    :param count: number of portions
    :param forward: s
    :param back:
    """
    for _ in range(portion):
        # portion move
        step(forward)
        # Safety anti-block solution?
        step(-back)
        step(back)
        step(-back)
        step(back)


def pinmap():
    """
    [i] micrOS LM naming convention
    Shows logical pins - pin number(s) used by this Load module
    - info which pins to use for this application
    :return dict: pin name (str) - pin value (int) pairs
    """
    p = servo_pinmap()
    p.update(stepper_pinmap())
    return p


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'serve portion=1 \t\t[info] servo control',  'serve_w_stepper portion=1 \t[info] stepper control'
