import asyncio
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False  # Disable hostname check
ssl_context.verify_mode = ssl.CERT_NONE  # Disable certificate verification


def open_connection(host, port, ssl=False):
    #return asyncio.open_connection(host, port, ssl=ssl)
    return asyncio.open_connection(host, port, ssl=ssl_context if ssl else None)


class Lock(asyncio.Lock):
    pass


class Event(asyncio.Event):
    pass


async def sleep(sec):
    await asyncio.sleep(sec)


async def sleep_ms(ms):
    await asyncio.sleep(ms/1000)


def get_event_loop():
    return asyncio.get_event_loop()


class Event:

    def __new__(cls):
        return asyncio.Event()


def start_server(awaitable, host, port, backlog):
    return asyncio.start_server(awaitable, host, port)







