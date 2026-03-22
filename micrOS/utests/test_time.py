import importlib.util
import sys
import types
import unittest
from pathlib import Path


def setUpModule():
    print(f"== RUN {Path(__file__).name} ==")


def _install_import_stubs(http_get_impl=None, cfg_store=None, log_store=None):
    cfg_store = {} if cfg_store is None else cfg_store
    log_store = [] if log_store is None else log_store

    m = types.ModuleType("machine")
    class RTC:
        def datetime(self, *_args, **_kwargs):
            return None
    m.RTC = RTC
    sys.modules["machine"] = m

    m = types.ModuleType("network")
    class WLAN:
        def __init__(self, *_args, **_kwargs):
            pass
        def isconnected(self):
            return True
    m.WLAN = WLAN
    m.STA_IF = 0
    sys.modules["network"] = m

    m = types.ModuleType("utime")
    m.sleep_ms = lambda *_a, **_k: None
    m.time = lambda: 1000
    m.mktime = lambda *_a, **_k: 0
    m.localtime = lambda *_a, **_k: (2026, 1, 1, 12, 0, 0, 3, 1)
    sys.modules["utime"] = m

    m = types.ModuleType("Config")
    def cfgget(key):
        defaults = {"utc": 60, "cron": True}
        return cfg_store.get(key, defaults.get(key))
    def cfgput(key, value, *_a, **_k):
        cfg_store[key] = value
        return True
    m.cfgget = cfgget
    m.cfgput = cfgput
    sys.modules["Config"] = m

    m = types.ModuleType("Debug")
    m.syslog = lambda msg, *_a, **_k: log_store.append(msg)
    m.console_write = lambda *_a, **_k: None
    sys.modules["Debug"] = m

    m = types.ModuleType("Files")
    class OSPath:
        DATA = "/tmp"
    m.OSPath = OSPath
    m.path_join = lambda *parts: "/".join(parts)
    sys.modules["Files"] = m

    m = types.ModuleType("urequests")
    m.get = http_get_impl or (lambda *_a, **_k: (500, ""))
    sys.modules["urequests"] = m
    return cfg_store, log_store


def _load_time_module(http_get_impl=None):
    cfg_store, log_store = _install_import_stubs(http_get_impl=http_get_impl)
    here = Path(__file__).resolve()
    time_path = (here.parent.parent / "source" / "Time.py").resolve()
    module_name = "micros_time_under_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, str(time_path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod, cfg_store, log_store


class TestTime(unittest.TestCase):
    def test_suntime_returns_cached_time_when_ip_api_response_is_invalid(self):
        mod, _cfg, logs = _load_time_module(http_get_impl=lambda *_a, **_k: (500, "bad"))
        mod.Sun.TIME = {"sunrise": (6, 0, 0), "sunset": (18, 0, 0)}
        self.assertEqual(mod.suntime(), mod.Sun.TIME)
        self.assertTrue(any("ip-api: invalid response" in msg for msg in logs))

    def test_suntime_uses_https_sunrise_endpoint_and_updates_utc(self):
        calls = []
        def fake_get(url, **kwargs):
            calls.append((url, kwargs))
            if "ip-api.com" in url:
                response = {"lat": 47.5, "lon": 19.0412, "timezone": "Europe/Budapest", "offset": 3600}
                print(f"[time-api] request url={url}")
                print(f"[time-api] response status=200 body={response!r}")
                return 200, response
            response = {"results": {"sunrise": "2026-01-01T06:30:00+00:00",
                                    "sunset": "2026-01-01T16:00:00+00:00"}}
            print(f"[time-api] request url={url}")
            print(f"[time-api] response status=200 body={response!r}")
            return 200, response
        mod, cfg, logs = _load_time_module(http_get_impl=fake_get)
        sun = mod.suntime()
        self.assertEqual(sun["sunrise"], (7, 30, 0))
        self.assertEqual(sun["sunset"], (17, 0, 0))
        self.assertEqual(cfg["utc"], 60)
        self.assertTrue(any(url.startswith("https://api.sunrise-sunset.org/") for url, _ in calls))
        self.assertFalse(any("sunrise-api" in msg for msg in logs))


if __name__ == "__main__":
    unittest.main(verbosity=2)
