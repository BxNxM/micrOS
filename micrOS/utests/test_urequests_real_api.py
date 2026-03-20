"""
Integration tests for source/urequests.py against public real endpoints.

These tests are skipped by default because they require internet access and
depend on third-party services being reachable.

Run explicitly:
  MICROS_REAL_API_TESTS=1 python3 -m unittest -v micrOS.utests.test_urequests_real_api
"""

import os
import sys
import ssl
import json
import types
import socket
import unittest
import importlib.util
from pathlib import Path


def _install_import_stubs():
    m = types.ModuleType("usocket")
    m.socket = socket.socket
    m.getaddrinfo = socket.getaddrinfo
    sys.modules["usocket"] = m

    m = types.ModuleType("ussl")
    m.wrap_socket = ssl.wrap_socket
    sys.modules["ussl"] = m

    m = types.ModuleType("uasyncio")
    async def open_connection(*args, **kwargs):
        import asyncio
        return await asyncio.open_connection(*args, **kwargs)
    m.open_connection = open_connection
    sys.modules["uasyncio"] = m

    m = types.ModuleType("Debug")
    m.syslog = lambda *_a, **_k: None
    sys.modules["Debug"] = m


def _load_urequests_module():
    here = Path(__file__).resolve()
    urequests_path = (here.parent.parent / "source" / "urequests.py").resolve()
    if not urequests_path.exists():
        raise FileNotFoundError(f"urequests.py not found at: {urequests_path}")

    _install_import_stubs()

    module_name = "micros_urequests_under_test"
    spec = importlib.util.spec_from_file_location(module_name, str(urequests_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {urequests_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


@unittest.skipUnless(
    os.environ.get("MICROS_REAL_API_TESTS") == "1",
    "Set MICROS_REAL_API_TESTS=1 to run real-network integration tests.",
)
class TestURequestsRealApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.urequests = _load_urequests_module()

    def test_http_get_json_ip_api(self):
        status, body = self.urequests.get(
            "http://ip-api.com/json/?fields=lat,lon,timezone,offset",
            jsonify=True,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(body, dict)
        self.assertIn("lat", body)
        self.assertIn("lon", body)
        self.assertIn("timezone", body)
        self.assertIn("offset", body)

    def test_https_get_json_sunrise_sunset(self):
        status, body = self.urequests.get(
            "https://api.sunrise-sunset.org/json?lat=47.4979&lng=19.0402&date=today&formatted=0",
            jsonify=True,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(body, dict)
        self.assertEqual(body.get("status"), "OK")
        results = body.get("results")
        self.assertIsInstance(results, dict)
        self.assertIn("sunrise", results)
        self.assertIn("sunset", results)

    def test_http_get_raw_body_is_json_text(self):
        status, body = self.urequests.get(
            "http://ip-api.com/json/?fields=lat,lon,timezone,offset",
            jsonify=False,
        )
        self.assertEqual(status, 200)
        self.assertIsInstance(body, str)
        parsed = json.loads(body)
        self.assertIn("lat", parsed)
        self.assertIn("lon", parsed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
