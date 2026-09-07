import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


SOURCE = Path(__file__).resolve().parent.parent / "source"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestTaskQueueMemoryPolicy(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config = types.ModuleType("Config")
        config.cfgget = lambda key: {"aioqueue": 5, "dbg": False}.get(key)
        config.cfgput = lambda *_args, **_kwargs: True

        debug = types.ModuleType("Debug")
        debug.console_write = lambda *_args, **_kwargs: None
        debug.syslog = lambda *_args, **_kwargs: None

        tasks = types.ModuleType("Tasks")
        tasks.TaskBase = type("TaskBase", (), {"QUEUE_SIZE": 5})
        tasks.exec_lm_pipe = lambda *_args, **_kwargs: True
        tasks.memory = lambda: 0

        auth = types.ModuleType("Auth")
        auth.resolve_secret = lambda value: value

        machine = types.ModuleType("machine")
        machine.freq = lambda *_args: 160_000_000

        stubs = {
            "Config": config,
            "Debug": debug,
            "Tasks": tasks,
            "Auth": auth,
            "machine": machine,
        }
        with mock.patch.dict(sys.modules, stubs):
            cls.hooks = _load_module("memory_policy_hooks", SOURCE / "Hooks.py")

    def test_low_memory_reduces_queue_to_one(self):
        with mock.patch.object(self.hooks, "memory", return_value=0), \
                mock.patch.object(self.hooks, "cfgget", return_value=5), \
                mock.patch.object(self.hooks, "cfgput") as cfgput:
            self.hooks._tune_queue_size()

        self.assertEqual(self.hooks.TaskBase.QUEUE_SIZE, 1)
        cfgput.assert_called_once_with("aioqueue", 1)

    def test_queue_is_still_capped_at_twenty(self):
        with mock.patch.object(self.hooks, "memory", return_value=1_000_000), \
                mock.patch.object(self.hooks, "cfgget", return_value=25), \
                mock.patch.object(self.hooks, "cfgput") as cfgput:
            self.hooks._tune_queue_size()

        self.assertEqual(self.hooks.TaskBase.QUEUE_SIZE, 20)
        cfgput.assert_called_once_with("aioqueue", 20)

    def test_zero_and_negative_queue_are_corrected_to_one(self):
        for configured_queue in (0, -1):
            with self.subTest(configured_queue=configured_queue), \
                    mock.patch.object(self.hooks, "memory", return_value=1_000_000), \
                    mock.patch.object(self.hooks, "cfgget", return_value=configured_queue), \
                    mock.patch.object(self.hooks, "cfgput") as cfgput:
                self.hooks._tune_queue_size()

                self.assertEqual(self.hooks.TaskBase.QUEUE_SIZE, 1)
                cfgput.assert_called_once_with("aioqueue", 1)


class TestRobustnessMemoryReport(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        lm_system = types.ModuleType("LM_system")
        lm_system.memory_usage = lambda: {"percent": 0, "mem_used": 0}

        common = types.ModuleType("Common")
        common.syslog = lambda *_args, **_kwargs: True
        def micro_task(*_args, **kwargs):
            if kwargs.get("_wrap"):
                return lambda function: function
            return None
        common.micro_task = micro_task

        auth = types.ModuleType("Auth")
        def sudo(function=None, **_kwargs):
            if function is not None:
                return function
            return lambda wrapped: wrapped
        auth.sudo = sudo

        stubs = {"LM_system": lm_system, "Common": common, "Auth": auth}
        with mock.patch.dict(sys.modules, stubs):
            cls.robustness = _load_module(
                "memory_policy_robustness", SOURCE / "modules" / "LM_robustness.py"
            )

    def test_memory_leak_reports_allocated_growth_as_positive(self):
        readings = iter((
            {"mem_used": 100},
            {"percent": 10.0},
            {"mem_used": 150},
        ))
        with mock.patch.object(
            self.robustness, "memory_usage", side_effect=lambda: next(readings)
        ):
            output = self.robustness.memory_leak(cnt=1)

        self.assertIn("RAM Alloc.: 0 kB 50 byte", output)


if __name__ == "__main__":
    unittest.main()
