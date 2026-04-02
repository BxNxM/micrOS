import importlib.util
import json
import sys
import tempfile
import types
import unittest
from itertools import count
from pathlib import Path
from unittest import mock


def setUpModule():
    print(f"== RUN {Path(__file__).name} ==")


_LOAD_ID = count()


class _ConfigStubEnv:
    def __init__(self, root: Path):
        self.root = root
        self.config_dir = root / "config"
        self.logs = []
        self.console = []
        self._saved = {}

    def _resolve(self, path):
        path = Path(path)
        return path if path.is_absolute() else self.root / path

    def install(self):
        for name in ("Debug", "Files", "uos", "microIO"):
            self._saved[name] = sys.modules.get(name)

        env = self

        debug_mod = types.ModuleType("Debug")

        class DebugCfg:
            DEBUG = True
            init_calls = 0

            @staticmethod
            def init_pled():
                DebugCfg.init_calls += 1

        debug_mod.DebugCfg = DebugCfg
        debug_mod.console_write = lambda msg, *_a, **_k: env.console.append(str(msg))
        debug_mod.syslog = lambda msg, *_a, **_k: env.logs.append(str(msg))
        sys.modules["Debug"] = debug_mod

        files_mod = types.ModuleType("Files")

        class OSPath:
            CONFIG = str(env.config_dir)

        def path_join(*parts):
            path = "/".join(str(part).strip("/") for part in parts if part)
            if parts and str(parts[0]).startswith("/"):
                path = path if path.startswith("/") else "/" + path
            return path

        files_mod.OSPath = OSPath
        files_mod.path_join = path_join
        files_mod.is_file = lambda path: env._resolve(path).is_file()
        sys.modules["Files"] = files_mod

        uos_mod = types.ModuleType("uos")
        uos_mod.remove = lambda path: env._resolve(path).unlink()
        uos_mod.rename = lambda src, dst: env._resolve(src).rename(env._resolve(dst))
        sys.modules["uos"] = uos_mod

        microio_mod = types.ModuleType("microIO")
        microio_mod.set_pinmap = None
        sys.modules["microIO"] = microio_mod

    def restore(self):
        for name, module in self._saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def _load_config_module(raw_config=None):
    tempdir = tempfile.TemporaryDirectory()
    root = Path(tempdir.name)
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = config_dir / "node_config.json"
    if raw_config is not None:
        config_path.write_text(raw_config, encoding="utf-8")

    env = _ConfigStubEnv(root)
    env.install()
    try:
        here = Path(__file__).resolve()
        config_py = (here.parent.parent / "source" / "Config.py").resolve()
        module_name = f"micros_config_under_test_{next(_LOAD_ID)}"
        spec = importlib.util.spec_from_file_location(module_name, str(config_py))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
        return mod, env, tempdir, config_path
    finally:
        env.restore()


class TestConfig(unittest.TestCase):
    def test_init_bootstraps_missing_config(self):
        mod, env, tempdir, config_path = _load_config_module()
        self.addCleanup(tempdir.cleanup)

        self.assertTrue(config_path.is_file())
        self.assertEqual(mod.cfgget("devfid"), "node01")
        self.assertFalse(any("read_cfg_file error" in msg for msg in env.logs))

        persisted = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["devfid"], "node01")
        self.assertEqual(persisted["appwd"], "ADmin123")

    def test_init_quarantines_corrupted_config_and_regenerates_defaults(self):
        raw_corrupt = '{"devfid": "broken"'
        mod, env, tempdir, config_path = _load_config_module(raw_config=raw_corrupt)
        self.addCleanup(tempdir.cleanup)

        bad_path = config_path.with_name("node_config.json.bad")
        self.assertTrue(bad_path.is_file())
        self.assertEqual(bad_path.read_text(encoding="utf-8"), raw_corrupt)
        self.assertEqual(mod.cfgget("devfid"), "node01")
        self.assertTrue(any("read_cfg_file error" in msg for msg in env.logs))

        persisted = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["devfid"], "node01")

    def test_cfgput_keeps_runtime_value_and_logs_when_write_fails(self):
        mod, env, tempdir, config_path = _load_config_module(raw_config='{"devfid": "orig"}')
        self.addCleanup(tempdir.cleanup)

        self.assertEqual(mod.cfgget("devfid"), "orig")
        with mock.patch("builtins.open", side_effect=OSError("disk full")):
            self.assertTrue(mod.cfgput("devfid", "updated"))
        self.assertEqual(mod.cfgget("devfid"), "updated")
        self.assertTrue(any("write_cfg_file" in msg for msg in env.logs))

        persisted = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["devfid"], "orig")


if __name__ == "__main__":
    unittest.main(verbosity=2)
