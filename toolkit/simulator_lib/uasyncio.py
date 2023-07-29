import asyncio


def open_connection(host, port):
    return asyncio.open_connection(host, port)


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







