import unittest
from  unittest import mock

import sys
import importlib.util
from pathlib import Path


def setUpModule():
    print(f"== RUN {Path(__file__).name} ==")


def _load_buffer_module():
    here = Path(__file__).resolve()
    buffer_path = (here.parent.parent / "source" / "Buffer.py").resolve()
    if not buffer_path.exists():
        raise FileNotFoundError(f"Buffer.py not found at: {buffer_path}")

    module_name = "micros_buffer_under_test"
    spec = importlib.util.spec_from_file_location(module_name, str(buffer_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {buffer_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


class BufferTestBase(unittest.TestCase):
    """
    Tests for the core functionality of the state machine.
    """
    buffer_type = bytearray

    def make_buffer(self, data):
        return self.buffer_type(data)

    @classmethod
    def setUpClass(cls):
        cls.buffer_module = _load_buffer_module()


    def setUp(self):
        self.buf = self.buffer_module.SlidingBuffer(self.make_buffer(8))


    def test_empty_buffer(self):
        self.assertEqual(self.buf.size(), 0)
        self.assertEqual(self.buf.capacity, 8)
        self.assertEqual(self.buf.readable_view(), b'')


    def test_write_and_peek(self):
        self.buf.write(b'ab')
        self.assertEqual(self.buf.size(), 2)
        self.assertEqual(self.buf.readable_view(), b'ab')
        self.assertEqual(self.buf.peek(), b'ab')
        self.assertEqual(self.buf.peek(2), b'ab')
        self.assertEqual(self.buf.peek(1), b'a')


    def test_zero_write(self):
        self.buf.write(b'')
        self.assertEqual(self.buf.size(), 0)


    def test_peek_invalid_index(self):
        self.buf.write(b'abcdef')
        with self.assertRaises(IndexError):
            self.buf.peek(-1)
        with self.assertRaises(IndexError):
            self.buf.peek(7)


    def test_consume(self):
        self.buf.write(b'ab')
        self.buf.consume(1)
        self.assertEqual(self.buf.readable_view(), b'b')
        self.buf.consume(1)
        self.assertEqual(self.buf.size(), 0)


    def test_consume_none(self):
        self.buf.write(b'abcdef')
        self.buf.consume(0)
        self.assertEqual(self.buf.readable_view(), b'abcdef')


    def test_consume_all(self):
        self.buf.write(b'abcdef')
        self.buf.consume()
        self.assertEqual(self.buf.readable_view(), b'')


    def test_consume_more(self):
        self.buf.write(b'abcdef')
        with self.assertRaises(ValueError):
            self.buf.consume(9)


    def test_overflow(self):
        self.buf.write(b'a' * 8)
        self.assertEqual(self.buf.size(), 8)
        with self.assertRaises(self.buffer_module.BufferFullError):
            self.buf.write(b'a')


    def test_compaction(self):
        self.buf.write(b'abcdefgh')
        self.buf.consume(2)
        self.buf.write(b'XY')  # should cause compaction internally
        self.assertEqual(bytes(self.buf.readable_view()), b'cdefghXY')
        self.assertEqual(self.buf.size(), 8)


    def test_multiple_compactions(self):
        for _ in range(20):
            self.buf.write(b'abcd')
            self.buf.consume(4)


    def test_find_term(self):
        self.buf.write(b'abcdefgh')
        self.assertEqual(self.buf.find(b'bc'), 1)
        self.assertEqual(self.buf.find(b'gh'), 6)
        self.assertEqual(self.buf.find(b'hi'), -1)

        self.buf.consume(3)
        self.buf.write(b'ghi')
        self.assertEqual(self.buf.find(b'fgh'), 2)


    def test_prepare_commit(self):
        self.buf.prepare(3)
        self.buf.commit(3)
        self.assertEqual(self.buf.size(),3)
        self.assertEqual(bytes(self.buf.readable_view()), b'\x00\x00\x00')


    def test_consume_prepare_insufficient(self):
        self.buf.write(b'abcdefgh')
        self.buf.consume(4)
        self.buf.prepare(4)
        with self.assertRaises(ValueError):
            self.buf.commit(5)


    def test_prepare_commit_none(self):
        self.buf.commit(0)


    def test_prepare_error(self):
        with self.assertRaises(ValueError):
            self.buf.prepare(9)


class TestWithBytearray(BufferTestBase):
    buffer_type = bytearray


class TestWithMemoryview(BufferTestBase):
    @staticmethod
    def buffer_type(data):
        return memoryview(bytearray(data))


if __name__ == "__main__":
    unittest.main(verbosity=2)
