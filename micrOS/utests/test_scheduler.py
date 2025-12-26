"""
Scheduler.py unit test (single 1-year execution, end-of-run metrics)

Run:
  python3 -m unittest -v utests.test_scheduler

This:
- loads ../source/Scheduler.py via importlib (no package needed)
- stubs external imports so Scheduler.py runs untouched
- simulates exactly RUN_DAYS days with virtual ticks
- calls Scheduler.scheduler(EXEC_PERIOD_SEC) in sync with the virtual tick step
- validates selected tasks via counts + ΔT metrics (requested vs executed time)
- prints one summary at the end (no per-tick spam; progress is throttled)
"""

from __future__ import annotations

import math
import os
import sys
import types
import unittest
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

# =============================================================================
# EDIT HERE: generic test tasks
# =============================================================================
# Each entry becomes a cron task: "<time_spec>!<lm_name>"
# time_spec formats:
#   WD:H:M:S  (WD can be '*', 0..6, or ranges like 0-4)
#   sunrise / sunset / sunrise+30 / sunset-15 (uses SUN_TIME mapping)
#
# NOTE: Builtins are always present in Scheduler.scheduler():
#   "*:3:0:0" -> suntime
#   "*:3:5:0" -> ntp_time
#
TEST_TASKS = [
    # Fires daily at noon
    {"lm": "LM_NOON", "time": "*:12:0:0", "expect_count": 365},

    # Weekday only at 08:30:00 (in a 365-day year starting WD=0, weekdays occur 261 times)
    {"lm": "LM_WEEKDAY_0830", "time": "0-4:8:30:0", "expect_count": 261},

    # Tag + offset example: daily at sunset-15
    {"lm": "LM_SUNSET_MINUS_15", "time": "sunset-15", "expect_count": 365},

    # Wildcard seconds example: every second during 12:00 minute (60 per day)
    # {"lm": "LM_STAR_SEC", "time": "*:12:0:*", "expect_count": 365 * 60},
]

# One-year run config
RUN_DAYS = 365

# Single knob used everywhere:
# - scheduler sampling/tolerance window (deltasec)
# - execution period (how frequently scheduler() is called)
# - virtual time tick step
EXEC_PERIOD_SEC = 5  # default 5 seconds

# Provide sunrise/sunset times for tag resolution (Sun.TIME)
SUN_TIME = {"sunrise": (6, 0, 0), "sunset": (18, 0, 0)}

# If set, prints extra details about each task summary
VERBOSE_SUMMARY = os.environ.get("SCHED_TEST_SUMMARY_VERBOSE", "0") == "1"


# =============================================================================
# Internal: stubs + module loader
# =============================================================================

def _install_import_stubs():
    """Install minimal stub modules so Scheduler.py imports succeed unchanged."""
    if "Tasks" not in sys.modules:
        m = types.ModuleType("Tasks")
        m.exec_lm_pipe_schedule = lambda *_a, **_k: True
        sys.modules["Tasks"] = m

    if "Debug" not in sys.modules:
        m = types.ModuleType("Debug")
        m.console_write = lambda *_a, **_k: None
        m.syslog = lambda *_a, **_k: None
        sys.modules["Debug"] = m

    if "Time" not in sys.modules:
        m = types.ModuleType("Time")

        class _Sun:
            TIME: Dict[str, Tuple[int, int, int]] = {}

        m.Sun = _Sun
        m.suntime = lambda: "stub_suntime"
        m.ntp_time = lambda: "stub_ntp_time"
        sys.modules["Time"] = m

    if "Config" not in sys.modules:
        m = types.ModuleType("Config")
        m.cfgget = lambda _k: ""
        sys.modules["Config"] = m


def _load_scheduler_module():
    here = Path(__file__).resolve()
    scheduler_path = (here.parent.parent / "source" / "Scheduler.py").resolve()
    if not scheduler_path.exists():
        raise FileNotFoundError(f"Scheduler.py not found at: {scheduler_path}")

    _install_import_stubs()

    module_name = "micros_scheduler_under_test_single"
    spec = importlib.util.spec_from_file_location(module_name, str(scheduler_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {scheduler_path}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


# =============================================================================
# Virtual time
# =============================================================================

def virtual_localtime_iter(
    days: int,
    step_sec: int,
    start_year: int = 2024,
    start_month: int = 1,
    start_day: int = 1,
    start_wd: int = 0,   # 0=Monday ... 6=Sunday
) -> Iterator[Tuple[int, int, int, int, int, int, int, int]]:
    """
    Generates valid localtime() tuples:
      (Y, M, D, H, M, S, WD, YD)

    step_sec controls tick rate (must match EXEC_PERIOD_SEC).
    """
    if step_sec <= 0:
        raise ValueError("step_sec must be >= 1")

    def is_leap(y: int) -> bool:
        return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

    mdays_common = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

    def month_len(y: int, mo: int) -> int:
        if mo == 2 and is_leap(y):
            return 29
        return mdays_common[mo - 1]

    y = start_year
    mo = start_month
    d = start_day
    wd = start_wd

    yday = 0
    for m in range(1, mo):
        yday += month_len(y, m)
    yday += (d - 1)

    for _day_idx in range(days):
        sec = 0
        while sec < 86400:
            s = sec % 60
            mi = (sec // 60) % 60
            h = (sec // 3600)
            yield (y, mo, d, h, mi, s, wd, yday)
            sec += step_sec

        # Advance date by 1 day
        yday += 1
        wd = (wd + 1) % 7
        d += 1
        if d > month_len(y, mo):
            d = 1
            mo += 1
            if mo > 12:
                mo = 1
                y += 1
                yday = 0


def _hhmmss_to_sec(h: int, m: int, s: int) -> int:
    return int(h) * 3600 + int(m) * 60 + int(s)


def _parse_tag_with_offset(tag: str) -> Tuple[str, int]:
    tag = tag.strip()
    if "+" in tag:
        base, off = tag.split("+", 1)
        return base.strip(), int(off.strip())
    if "-" in tag:
        base, off = tag.split("-", 1)
        return base.strip(), -int(off.strip())
    return tag, 0


def _requested_hms_for_spec(time_spec: str) -> Tuple[int, int, int]:
    """
    Convert 'sunset-15' or 'sunrise+30' to absolute HMS based on SUN_TIME.
    For WD:H:M:S specs, returns H,M,S if fixed, else returns 0,0,0 (handled elsewhere).
    """
    time_spec = time_spec.strip()
    if ":" in time_spec:
        parts = [p.strip() for p in time_spec.split(":")]
        h = parts[1] if len(parts) > 1 else "*"
        m = parts[2] if len(parts) > 2 else "*"
        s = parts[3] if len(parts) > 3 else "*"
        if h.isdigit() and m.isdigit() and s.isdigit():
            return int(h), int(m), int(s)
        return 0, 0, 0

    base, offset_min = _parse_tag_with_offset(time_spec)
    h, m, s = SUN_TIME[base]
    total_min = (h * 60 + m) + offset_min
    total_min %= 1440
    return int(total_min // 60), int(total_min % 60), int(s)


# =============================================================================
# Metrics aggregator (no per-event storage)
# =============================================================================

@dataclass
class Agg:
    count: int = 0
    pass_count: int = 0
    min_dt: int = 0
    max_dt: int = 0
    sum_dt: int = 0
    sumsq_dt: int = 0

    def add(self, dt: int, tol: int):
        if self.count == 0:
            self.min_dt = dt
            self.max_dt = dt
        else:
            self.min_dt = min(self.min_dt, dt)
            self.max_dt = max(self.max_dt, dt)

        self.count += 1
        self.sum_dt += dt
        self.sumsq_dt += dt * dt
        if -tol <= dt <= tol:
            self.pass_count += 1

    def stats(self) -> Tuple[float, float]:
        if self.count == 0:
            return 0.0, 0.0
        mean = self.sum_dt / self.count
        var = (self.sumsq_dt / self.count) - (mean * mean)
        std = math.sqrt(var) if var > 0 else 0.0
        return mean, std


# =============================================================================
# The test
# =============================================================================

class TestSchedulerSingleYearMetrics(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.S = _load_scheduler_module()

    def setUp(self):
        self.S.LAST_CRON_TASKS.clear()

    def test_one_year_metrics_and_counts(self):
        S = self.S

        # Build cron_data string from TEST_TASKS
        cron_data = ";".join(f"{t['time']}!{t['lm']}" for t in TEST_TASKS)

        aggs: Dict[str, Agg] = {
            "BUILTIN:suntime": Agg(),
            "BUILTIN:ntp_time": Agg(),
        }
        expected_counts: Dict[str, int] = {
            "BUILTIN:suntime": RUN_DAYS,
            "BUILTIN:ntp_time": RUN_DAYS,
        }

        time_spec_by_lm: Dict[str, str] = {}
        for t in TEST_TASKS:
            key = f"LM:{t['lm']}"
            aggs[key] = Agg()
            expected_counts[key] = int(t["expect_count"])
            time_spec_by_lm[t["lm"]] = str(t["time"])

        # Patch Scheduler dependencies in-module
        S.console_write = lambda *_a, **_k: None
        S.syslog = lambda *_a, **_k: None
        S.cfgget = lambda k: cron_data if k == "crontasks" else ""

        class _SunObj:
            TIME = dict(SUN_TIME)

        S.Sun = _SunObj

        current_localtime: Optional[Tuple[int, int, int, int, int, int, int, int]] = None

        def fake_localtime():
            return current_localtime  # type: ignore[return-value]

        S.localtime = fake_localtime

        def _record(key: str, req_h: int, req_m: int, req_s: int):
            nonlocal current_localtime
            assert current_localtime is not None
            _, _, _day, ah, am, asec, _wd, _yd = current_localtime

            act_sec = _hhmmss_to_sec(ah, am, asec)
            req_sec = _hhmmss_to_sec(req_h, req_m, req_s)
            dt = act_sec - req_sec
            aggs[key].add(dt, tol=EXEC_PERIOD_SEC)

        def fake_suntime():
            _record("BUILTIN:suntime", 3, 0, 0)
            return "sun ok"

        def fake_ntp_time():
            _record("BUILTIN:ntp_time", 3, 5, 0)
            return "ntp ok"

        S.suntime = fake_suntime
        S.ntp_time = fake_ntp_time

        def fake_exec_lm_pipe_schedule(cmd: str):
            cmd = str(cmd).strip()
            time_spec = time_spec_by_lm.get(cmd, "")

            if ":" in time_spec:
                parts = [p.strip() for p in time_spec.split(":")]
                h_spec = parts[1] if len(parts) > 1 else "*"
                m_spec = parts[2] if len(parts) > 2 else "*"
                s_spec = parts[3] if len(parts) > 3 else "*"

                assert current_localtime is not None
                _, _, _day, ah, am, asec, _wd, _yd = current_localtime

                req_h = ah if h_spec == "*" else int(h_spec)
                req_m = am if m_spec == "*" else int(m_spec)
                req_s = asec if s_spec == "*" else int(s_spec)
                _record(f"LM:{cmd}", req_h, req_m, req_s)
            else:
                req_h, req_m, req_s = _requested_hms_for_spec(time_spec)
                _record(f"LM:{cmd}", req_h, req_m, req_s)

            return True

        S.exec_lm_pipe_schedule = fake_exec_lm_pipe_schedule

        # Run exactly one year, tick + scheduler call step = EXEC_PERIOD_SEC
        t_iter = virtual_localtime_iter(days=RUN_DAYS, step_sec=EXEC_PERIOD_SEC)

        # Progressbar throttling (avoid printing millions of times)
        last_percent_int = -1

        print(f"\n== RUN CRON-SCHEDULER TEST {RUN_DAYS} days")
        for lt in t_iter:
            # Progressbar (based on yday + fraction of day)
            progressbar_width: int = 50
            yd = lt[7]  # 0-based day index
            sec_in_day = (lt[3] * 3600) + (lt[4] * 60) + lt[5]
            percent: float = (yd + (sec_in_day / 86400.0)) / float(RUN_DAYS)
            if percent < 0.0:
                percent = 0.0
            elif percent > 1.0:
                percent = 1.0

            percent_int = int(percent * 100)
            if percent_int != last_percent_int:
                last_percent_int = percent_int
                filled = int(progressbar_width * percent)
                progressbar: str = f"{'|' * filled}{' ' * (progressbar_width - filled)}"
                print(f"({EXEC_PERIOD_SEC} sec timer): {lt}\t|{progressbar}| {percent_int} %", end="\r")

            # RUN:
            current_localtime = lt
            S.scheduler(EXEC_PERIOD_SEC)

        # ---- Final verdict summary
        calls = RUN_DAYS * (86400 // EXEC_PERIOD_SEC)

        lines: List[str] = []
        lines.append("=== Scheduler 1-year metrics ===")
        lines.append(f"days={RUN_DAYS}, exec_period={EXEC_PERIOD_SEC}s, calls~={calls}, tol=±{EXEC_PERIOD_SEC}s")
        lines.append(f"cron_data='{cron_data}'")
        lines.append("")

        any_fail = False

        for key in sorted(aggs.keys()):
            agg = aggs[key]
            exp = expected_counts.get(key, None)
            mean, std = agg.stats()
            pass_rate = (agg.pass_count / agg.count * 100.0) if agg.count else 0.0

            lines.append(
                f"{key:22s} "
                f"count={agg.count:6d} exp={exp if exp is not None else '-':6} "
                f"ΔT[min/avg/max]={agg.min_dt:+4d}/{mean:+6.2f}/{agg.max_dt:+4d} s "
                f"std={std:5.2f} "
                f"pass={agg.pass_count:6d} ({pass_rate:6.2f}%)"
            )

            if exp is not None and agg.count != exp:
                any_fail = True
            if agg.count and agg.pass_count != agg.count:
                any_fail = True

        summary = "\n".join(lines)
        print("\n" + summary)

        if any_fail:
            mismatches = []
            for key in sorted(aggs.keys()):
                agg = aggs[key]
                exp = expected_counts.get(key, None)
                if exp is not None and agg.count != exp:
                    mismatches.append(f"{key}: expected count {exp}, got {agg.count}")
                if agg.count and agg.pass_count != agg.count:
                    mismatches.append(f"{key}: {agg.count - agg.pass_count} executions outside ±{EXEC_PERIOD_SEC}s tolerance")

            self.fail("Scheduler validation failed:\n" + "\n".join(mismatches) + "\n\n" + summary)

        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
