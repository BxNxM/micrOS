"""
MICROPYTHON REPL micrOS Cli over UART
    - reset()    - reboot board
    - shell()    - start async micrOS shell (same as ShellCli)
"""

from time import sleep
from uos import listdir
from machine import soft_reset, reset as hard_reset

try:
    from Shell import Shell
    from Tasks import Manager
    from Common import micro_task
    # --- nonblocking stdin line reader (USB serial REPL) ---
    import sys, uselect
    _poll = uselect.poll()
    _poll.register(sys.stdin, uselect.POLLIN)
    _buf = []
except ImportError as e:
    print(f"!!!Cannot import shell: {e}")
    Shell = None

#############################################
#               REBOOT DEVICE               #
#############################################

def reset():
    """
    [HELPER] Reboot board
    """
    print('Device reboot now, boot micrOSloader...')
    sleep(1)

    if "main.py" in listdir():
        soft_reset()
    else:
        hard_reset()

#############################################
#               SHELL in REPL               #
#############################################

def _read_line_nb(echo=True):
    """
    Non-blocking:
      - returns a full line (str, without trailing newline) when '\n' received
      - returns None if no complete line yet
    Echoes typed characters and supports backspace locally.
    """
    while _poll.poll(0):              # check without waiting
        ch = sys.stdin.read(1)
        if not ch:
            break

        if ch == '\n':                # end-of-line (LF)
            line = ''.join(_buf)
            _buf.clear()
            return line               # NOTE: we do NOT print a newline
        if ch == '\r':                # ignore CR
            continue

        # backspace / delete
        if ch in ('\x08', '\x7f'):
            if _buf and echo:
                _buf.pop()
                sys.stdout.write('\x08 \x08')  # erase last char visually
            elif _buf:
                _buf.pop()
            continue

        # regular char
        _buf.append(ch)
        if echo:
            sys.stdout.write(ch)
    return None


async def _shell_task(task_id):

    class ReplShell(Shell):
        async def a_send(self, msg):
            print(f"\n{msg}", end='')

    shell_inst = ReplShell()
    with micro_task(task_id) as my_task:
        # Init shell welcome msg in repl mode
        await shell_inst.shell("help")
        # Run shell interpreter
        while True:
            my_task.out = "ShellCli in REPL"
            _msg = _read_line_nb()          # NoN Blocking ...
            #_msg = input()                 # Blocking input handling
            if _msg is not None:
                state = await shell_inst.shell(_msg)
                if not state or _msg.strip() == "exit":
                    print(f"\nEXIT SHELL: {_msg} ({state}) [Ctrl-C to return micropython repl]")
                    break
            await my_task.feed(sleep_ms=10)
    return f"Shell in REPL stopped...({state})"


def shell():
    """
    [HELPER] Run Shell in REPL
    """
    if Shell is None:
        return "Cannot run Shell in REPL, import error"
    # Prepare micrOS Task manager
    aio = Manager()
    # Initiate Shell as repl task
    task_id = "repl.shell"
    aio.create_task(callback=_shell_task(task_id), tag=task_id)
    # Run async main event loop
    aio.run_forever()
    return "Async Main Event Loop Stopped"


if __name__ == "helpers":
    # COMMAND LINE INTERFACE
    print("\nmicrOS REPL Tools\n-----------------")
    print("\t[0]  helpers.reset()  -  reboot board")
    if Shell: print("\t[1]  helpers.shell()  -  Start Shell in REPL")
    CHOICES = (reset, shell)
    CHOICE = None
    try:
        CHOICE = input("Select option: ").strip()
        CHOICE = int(CHOICE)
        # EXEC COMMAND
        CHOICES[CHOICE]()
    except Exception as e:
        print(f"Invalid input {CHOICE}: {e}")
