"""
Data structures for buffered processing & streaming
"""

class BufferFullError(RuntimeError):
    """Custom exception for writes exceeding buffer capacity"""
    pass


class MemoryPool:
    """
    Preallocated bytearray-backed memory pool that returns reusable memoryview slices
    for coroutine-based streaming without additional heap allocation.
    """
    __slots__ = ("_pool", "_blocks", "free")

    def __init__(self, block_size, block_count, wrapper=None):
        """
        Initialize memory pool
        :param block_size: size of each memory block in bytes
        :param block_count: number of reservable memory blocks
        :param wrapper: wrapper class (abstraction layer) to access the memory, e.g. SlidingBuffer
        """
        self._pool = bytearray(block_size * block_count)
        self._blocks = [
            memoryview(self._pool)[i*block_size:(i+1)*block_size] if wrapper is None
            else wrapper(memoryview(self._pool)[i*block_size:(i+1)*block_size])
            for i in range(block_count)
        ]
        self.free = list(self._blocks)

    def reserve(self):
        if self.free:
            return self.free.pop()

    def release(self, block):
        self.free.append(block)


class SlidingBuffer:
    """
    A linear sliding-window buffer over a fixed-size bytearray or its memoryview.

    'start' and 'end' indices are maintained, such that
    the readable region is always buffer[start:end], and the writeable
    region is buffer[end:capacity], with the following invariant:
    0 <= start <= end <= capacity

    Key features:
    - Zero-copy access via memoryview slices for both readable and writable regions
    - Incremental consumption by advancing 'start'
    - Incremental writes by advancing 'end'
    - Automatic in-place compaction when additional space is
    required and unused bytes exist before 'start'
    - Bounded memory usage; no dynamic reallocation
    """
    __slots__ = ("_buffer", "_start", "_end", "_mv", "capacity")

    def __init__(self, buffer: bytearray|memoryview):
        self._buffer = buffer
        self._start = 0
        self._end = 0
        self._mv = memoryview(self._buffer)
        self.capacity = len(buffer)

    def size(self) -> int:
        """Determine the window size"""
        return self._end - self._start

    def writable(self) -> int:
        """Determine the writeable size of the buffer"""
        return self.capacity - self._end

    def readable_view(self) -> memoryview:
        """Return a memoryview to the readable region of the buffer (window)"""
        return self._mv[self._start:self._end]

    def writable_view(self) -> memoryview:
        """Return a memoryview to the writeable region of the buffer"""
        return self._mv[self._end:self.capacity]

    def _compact(self):
        """
        Compact the buffer by shifting the active
        window to the beginning of the bytearray
        """
        if self._start == 0:
            return
        buf = self._buffer
        n = self._end - self._start
        for i in range(n):
            buf[i] = buf[self._start + i]
        self._start = 0
        self._end = n

    def peek(self, n=None) -> memoryview:
        """
        Return the first n bytes from the window,
        return the entire window when n is undefined
        """
        if n is None:
            n = self.size()
        if n > self.size() or n < 0:
            raise IndexError()
        return self._mv[self._start:self._start + n]

    def write(self, data:bytes):
        """Write new data into the writable region and advance the 'end' index"""
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("write() expects bytes or bytearray")
        needed = len(data)
        if needed > self.capacity - self._end:
            self._compact()
            if needed > self.capacity - self._end:
                raise BufferFullError()
        buf = self._buffer
        for i in range(needed):
            buf[self._end + i] = data[i]
        self._end += needed

    def consume(self, n: int=None):
        """Discard the first n bytes of the window by advancing the 'start' index"""
        if n is None:
            n = self.size()
        if n > self.size():
            raise ValueError("Buffer underflow")
        self._start += n
        if self._start == self._end:
            self._start = 0
            self._end = 0

    def prepare(self, n: int):
        """
        Check if the writeable region is larger or equal to n,
        otherwise attempt to compact the buffer
        """
        if n > self.capacity:
            raise ValueError("Capacity exceeded")

        if n > self.writable():
            self._compact()
            if n > self.writable():
                raise ValueError("Capacity exceeded")

    def commit(self, n):
        """Increase the window size by n bytes by incrementing the 'end' index"""
        if self._end + n > self.capacity:
            raise ValueError("Capacity exceeded")
        self._end += n

    def find(self, term: bytes) -> int:
        """Find and return the index of a search term in the current window"""
        for i in range(self._start, self._end - len(term) + 1):
            if self._mv[i : i+len(term)] == term:
                return i - self._start
        return -1
