import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


def setUpModule():
    print(f"== RUN {Path(__file__).name} ==")


PACKAGE = "test_package"
PACKAGE_REF = f"github:test/micrOSPackages/{PACKAGE}"
DEPENDENCY = "test_dependency"
MISSING_DEPENDENCY = "missing_dependency"


class _PacmanStubEnv:
    def __init__(self, root: Path):
        self.root = root
        self.lib = root / "lib"
        self.modules = root / "modules"
        self.web = root / "web"
        self.data = root / "data"
        self.config = root / "config"
        self.package_dir = self.lib / PACKAGE
        self.pacman_json = self.package_dir / "pacman.json"
        self.dependency_dir = self.lib / DEPENDENCY
        self.dependency_json = self.dependency_dir / "pacman.json"
        self._saved = {}
        self._install_count = 0
        self.logs = []

    def _receipt(self, version):
        return {
            "versions": {"packager": "0.2.0", "package": version},
            "url": PACKAGE_REF,
            "layout": {
                "/modules": ["LM_test.py"],
                "/data": [],
                "/web": ["index.html"],
            },
            "deps": [DEPENDENCY],
        }

    def _write_receipt(self, version):
        self.package_dir.mkdir(parents=True, exist_ok=True)
        content = json.dumps(self._receipt(version), indent=2)
        self.pacman_json.write_text(content, encoding="utf-8")
        return content

    def _write_dependency_receipt(self):
        self.dependency_dir.mkdir(parents=True, exist_ok=True)
        content = {
            "versions": {"packager": "0.2.0", "package": "0.0.1"},
            "url": f"github:test/micrOSPackages/{DEPENDENCY}",
            "layout": {"/modules": ["LM_dep.py"], "/data": [], "/web": []},
            "deps": [],
        }
        self.dependency_json.write_text(json.dumps(content, indent=2), encoding="utf-8")

    def install(self):
        for path in (self.lib, self.modules, self.web, self.data, self.config):
            path.mkdir()

        for name in ("Auth", "Common", "Debug", "Files", "mip", "Pacman", "uos", "urequests"):
            self._saved[name] = sys.modules.get(name)

        env = self

        auth_mod = types.ModuleType("Auth")

        def sudo(func=None, **_kwargs):
            def decorator(callback):
                return callback
            return decorator if func is None else decorator(func)

        auth_mod.sudo = sudo
        sys.modules["Auth"] = auth_mod

        common_mod = types.ModuleType("Common")
        common_mod.socket_stream = lambda callback: callback
        sys.modules["Common"] = common_mod

        debug_mod = types.ModuleType("Debug")
        debug_mod.console_write = lambda *_a, **_k: None
        debug_mod.syslog = lambda msg, *_a, **_k: env.logs.append(str(msg))
        sys.modules["Debug"] = debug_mod

        files_mod = types.ModuleType("Files")

        class OSPath:
            _ROOT = str(env.root)
            CONFIG = str(env.config)
            DATA = str(env.data)
            LIB = str(env.lib)
            MODULES = str(env.modules)
            WEB = str(env.web)

        def path_join(*parts):
            path = "/".join(str(part).strip("/") for part in parts if part)
            if parts and str(parts[0]).startswith("/"):
                path = path if path.startswith("/") else "/" + path
            return path

        def list_fs(path="/", type_filter="*", **_kwargs):
            items = sorted(Path(path).iterdir())
            if type_filter == "d":
                return [item.name for item in items if item.is_dir()]
            return [item.name for item in items]

        def remove_file(path, *_a, **_k):
            Path(path).unlink()
            return f"{path} deleted"

        def remove_dir(path, *_a, **_k):
            for item in Path(path).iterdir():
                if item.is_dir():
                    remove_dir(item)
                else:
                    item.unlink()
            Path(path).rmdir()
            return f"{path} deleted"

        files_mod.OSPath = OSPath
        files_mod.path_join = path_join
        files_mod.list_fs = list_fs
        files_mod.ilist_fs = lambda *_a, **_k: ()
        files_mod.is_dir = lambda path: Path(path).is_dir()
        files_mod.is_file = lambda path: Path(path).is_file()
        files_mod.remove_file = remove_file
        files_mod.remove_dir = remove_dir
        files_mod.is_protected = lambda _path: False
        sys.modules["Files"] = files_mod

        uos_mod = types.ModuleType("uos")
        uos_mod.mkdir = lambda path: Path(path).mkdir()
        uos_mod.rename = lambda source, target: Path(source).rename(target)
        sys.modules["uos"] = uos_mod

        mip_mod = types.ModuleType("mip")

        def mip_install(_ref, **_kwargs):
            env._install_count += 1
            version = "0.0.1" if env._install_count == 1 else "0.0.2"
            env._write_receipt(version)
            env._write_dependency_receipt()
            (env.lib / "LM_test.py").write_text("# test module\n", encoding="utf-8")
            (env.lib / "LM_dep.py").write_text("# dependency module\n", encoding="utf-8")
            (env.lib / "index.html").write_text("<h1>loose</h1>\n", encoding="utf-8")
            (env.package_dir / "index.html").write_text("<h1>test</h1>\n", encoding="utf-8")

        mip_mod.install = mip_install
        sys.modules["mip"] = mip_mod

        urequests_mod = types.ModuleType("urequests")
        urequests_mod.get = lambda **_kwargs: (200, {"version": "0.0.2"})
        sys.modules["urequests"] = urequests_mod

        _load_core_pacman()

    def restore(self):
        for name, module in self._saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def _load_lm_pacman():
    here = Path(__file__).resolve()
    lm_pacman_path = (here.parent.parent / "source" / "modules" / "LM_pacman.py").resolve()
    spec = importlib.util.spec_from_file_location("lm_pacman_under_test", str(lm_pacman_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_core_pacman():
    here = Path(__file__).resolve()
    pacman_path = (here.parent.parent / "source" / "Pacman.py").resolve()
    spec = importlib.util.spec_from_file_location("Pacman", str(pacman_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules["Pacman"] = module
    spec.loader.exec_module(module)
    return module


def _show(command, output):
    print(f"\n$ pacman {command}")
    print(output)
    return output


class TestPacmanLifecycle(unittest.TestCase):
    def test_unpack_resource_paths_and_invalid_dependency(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        env = _PacmanStubEnv(Path(tempdir.name))
        env.install()
        self.addCleanup(env.restore)
        pacman = sys.modules["Pacman"]

        env._write_dependency_receipt()
        (env.lib / "LM_dep.py").write_text("# dependency module\n", encoding="utf-8")
        env.package_dir.mkdir()
        env.pacman_json.write_text(
            json.dumps({
                "layout": {
                    "/web": ["data/icon.png", "matrix/matrix_draw.html", "../config/bad.txt"],
                    "/web/matrix": ["background.png"],
                },
                "deps": [DEPENDENCY, MISSING_DEPENDENCY, "../config"],
            }, indent=2),
            encoding="utf-8",
        )
        (env.package_dir / "matrix").mkdir()
        (env.package_dir / "icon.png").write_text("icon\n", encoding="utf-8")
        (env.package_dir / "background.png").write_text("root background\n", encoding="utf-8")
        (env.package_dir / "matrix" / "matrix_draw.html").write_text("<html>\n", encoding="utf-8")
        (env.package_dir / "matrix" / "background.png").write_text("background\n", encoding="utf-8")
        (env.config / "pacman.json").write_text(
            json.dumps({"layout": {"/modules": ["LM_bad.py"]}}),
            encoding="utf-8",
        )
        (env.lib / "LM_bad.py").write_text("# must remain packed\n", encoding="utf-8")

        unpacked = _show(f"unpack {PACKAGE}", pacman._unpack_from_pacman_json(str(env.lib), (PACKAGE,)))
        self.assertEqual(
            unpacked,
            f"\n    UNPACKING {env.pacman_json}"
            f"\n    UNPACKING {env.dependency_json}"
            f"\n  ✓ Unpacked LM_dep.py -> {env.modules}"
            f"\n  ! Skip dep unpack - metadata not found: {MISSING_DEPENDENCY}"
            f"\n  ✓ Unpacked data/icon.png -> {env.web}"
            f"\n  ✓ Unpacked matrix/matrix_draw.html -> {env.web}"
            f"\n  ✗ Invalid source: ../config/bad.txt"
            f"\n  ✓ Unpacked background.png -> {env.web / 'matrix'}",
        )
        self.assertTrue((env.web / "data" / "icon.png").is_file())
        self.assertTrue((env.web / "matrix" / "matrix_draw.html").is_file())
        self.assertTrue((env.web / "matrix" / "background.png").is_file())
        self.assertEqual((env.web / "matrix" / "background.png").read_text(encoding="utf-8"), "background\n")
        self.assertFalse((env.modules / "LM_bad.py").exists())

        removed = _show(f"uninstall {PACKAGE}", pacman.uninstall(PACKAGE))
        for path in (
            env.web / "data" / "icon.png",
            env.web / "matrix" / "matrix_draw.html",
            env.web / "matrix" / "background.png",
        ):
            self.assertIn(f"  ✓ Removed: {path}", removed)
            self.assertFalse(path.exists())

    def test_install_update_inspect_uninstall(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        env = _PacmanStubEnv(Path(tempdir.name))
        env.install()
        self.addCleanup(env.restore)
        lm_pacman = _load_lm_pacman()

        installed = _show(f'install "{PACKAGE_REF}"', lm_pacman.install(PACKAGE_REF))
        self.assertEqual(
            installed,
            f"[mip] Installing: {PACKAGE_REF} {{'target': '{env.lib}'}}\n"
            f"  ✓ Installed under {env.lib}\n"
            f"    UNPACKING {env.pacman_json}\n"
            f"    UNPACKING {env.dependency_json}\n"
            f"  ✓ Unpacked LM_dep.py -> {env.modules}\n"
            f"  ✓ Unpacked LM_test.py -> {env.modules}\n"
            f"  ✓ Unpacked index.html -> {env.web}",
        )
        self.assertTrue((env.modules / "LM_dep.py").is_file())
        self.assertTrue((env.modules / "LM_test.py").is_file())
        self.assertTrue((env.web / "index.html").is_file())
        self.assertEqual((env.web / "index.html").read_text(encoding="utf-8"), "<h1>test</h1>\n")

        self.assertEqual(_show("inspect", lm_pacman.inspect()), [DEPENDENCY, PACKAGE])

        inspected = _show(f"inspect {PACKAGE}", lm_pacman.inspect(PACKAGE))
        self.assertEqual(inspected, env.pacman_json.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(inspected)["versions"]["package"], "0.0.1")

        updated = _show(f"upgrade {PACKAGE}", lm_pacman.upgrade(PACKAGE))
        self.assertEqual(
            updated,
            f"Upgrade: collecting package info {PACKAGE}\n"
            f"  ✓ Upgrade package (0.0.1->0.0.2): {PACKAGE_REF}\n"
            f"[mip] Installing: {PACKAGE_REF} {{'target': '{env.lib}'}}\n"
            f"  ✓ Installed under {env.lib}\n"
            f"    UNPACKING {env.pacman_json}\n"
            f"    UNPACKING {env.dependency_json}\n"
            f"  ✓ Unpacked LM_dep.py -> {env.modules}\n"
            f"  ✓ Unpacked LM_test.py -> {env.modules}\n"
            f"  ✓ Unpacked index.html -> {env.web}",
        )

        inspected = _show(f"inspect {PACKAGE}", lm_pacman.inspect(PACKAGE))
        self.assertEqual(inspected, env.pacman_json.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(inspected)["versions"]["package"], "0.0.2")

        removed = _show(f"uninstall {PACKAGE}", lm_pacman.uninstall(PACKAGE))
        self.assertEqual(
            removed,
            f"Uninstall {PACKAGE}\n"
            f"  ✓ Removed: {env.modules / 'LM_test.py'}\n"
            f"  ✓ Removed: {env.web / 'index.html'}\n"
            f"  ! Skip dep delete: ['{DEPENDENCY}']\n"
            f"  {env.package_dir} deleted",
        )
        self.assertFalse(env.package_dir.exists())
        self.assertTrue((env.modules / "LM_dep.py").is_file())
        self.assertEqual(_show("inspect", lm_pacman.inspect()), [DEPENDENCY])


if __name__ == "__main__":
    unittest.main(verbosity=2)
