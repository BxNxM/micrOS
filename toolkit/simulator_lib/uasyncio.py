import asyncio
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False  # Disable hostname check
ssl_context.verify_mode = ssl.CERT_NONE  # Disable certificate verification

class TimeoutError(Exception):
    pass

def open_connection(host, port, ssl=False):
    #return asyncio.open_connection(host, port, ssl=ssl)
    return asyncio.open_connection(host, port, ssl=ssl_context if ssl else None)


class Lock(asyncio.Lock):
    pass


class Event(asyncio.Event):
    pass


async def wait_for(fut, timeout):
    return asyncio.wait_for(fut, timeout)


async def sleep(sec):
    await asyncio.sleep(sec)


async def sleep_ms(ms):
    await asyncio.sleep(ms/1000)


def get_event_loop():
    """
    Returns asyncio.EventLoop
    """
    try:
        # LEGACY: NOT WORKS FROM PYTHON 3.13
        # BUT THIS IS THE MICROPYTHON WAY...
        return asyncio.get_event_loop()
    except Exception as e:
        print(f"[SIM] get_event_loop exception: {e}")
    # PYTHON <3.13 NEW WAY
    try:
        # Check running event loop
        # MICROPYTHON HAS A SINGLE EVENT LOOP
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Create event loop with new method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    # return new "singleton" event loop
    return loop


class Event:

    def __new__(cls):
        return asyncio.Event()


def start_server(awaitable, host, port, backlog):
    return asyncio.start_server(awaitable, host, port)







