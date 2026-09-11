"""
Validates the live-session detection logic by pretending "now" is a moment
during the 2024 Abu Dhabi GP race (a real, already-recorded session) — since
no GP is actually live right now, this is the only way to exercise the
time-window math against real schedule data without waiting for a real race.
"""
import unittest.mock as mock

import pandas as pd
import fastf1

from data.loader import CACHE_DIR
fastf1.Cache.enable_cache(str(CACHE_DIR))

from data import loader

YEAR, GP = 2024, "Abu Dhabi Grand Prix"
# Session5 (Race) started at 2024-12-08 13:00:00 UTC per the schedule.
DURING_RACE_UTC = pd.Timestamp("2024-12-08 13:45:00")
BEFORE_WEEKEND_UTC = pd.Timestamp("2024-12-01 10:00:00")
LONG_AFTER_UTC = pd.Timestamp("2024-12-09 20:00:00")


def fake_now(tz=None):
    base = {
        "during": DURING_RACE_UTC,
        "before": BEFORE_WEEKEND_UTC,
        "after": LONG_AFTER_UTC,
    }[CURRENT_SCENARIO]
    if tz is not None:
        return base.tz_localize("UTC")
    # naive "local" now used by get_selectable_event_names; keep close to race day
    return {
        "during": pd.Timestamp("2024-12-08 17:45:00"),
        "before": pd.Timestamp("2024-12-01 14:00:00"),
        "after": pd.Timestamp("2024-12-09 20:00:00"),
    }[CURRENT_SCENARIO]


results = []


def check(label, fn):
    try:
        out = fn()
        results.append((label, "OK", out))
    except Exception as e:
        results.append((label, "FAIL", repr(e)))


def clear_caches():
    loader.get_selectable_event_names.clear()
    loader.get_available_session_codes.clear()


with mock.patch.object(pd.Timestamp, "now", staticmethod(fake_now)):
    CURRENT_SCENARIO = "during"
    clear_caches()
    check("is_session_live(during race) == True", lambda: loader.is_session_live(YEAR, GP, "R") is True)
    check("R in available_codes(during race)", lambda: "R" in loader.get_available_session_codes(YEAR, GP))
    check("event selectable(during race)", lambda: GP in loader.get_selectable_event_names(YEAR))

    CURRENT_SCENARIO = "before"
    clear_caches()
    check("is_session_live(before weekend) == False", lambda: loader.is_session_live(YEAR, GP, "R") is False)
    check("R not in available_codes(before weekend)", lambda: "R" not in loader.get_available_session_codes(YEAR, GP))
    check("FP1 not in available_codes(before weekend)", lambda: "FP1" not in loader.get_available_session_codes(YEAR, GP))
    check("event NOT selectable(3 weeks before)", lambda: GP not in loader.get_selectable_event_names(YEAR))

    CURRENT_SCENARIO = "after"
    clear_caches()
    check("is_session_live(long after) == False", lambda: loader.is_session_live(YEAR, GP, "R") is False)
    check("R in available_codes(long after, all started)", lambda: "R" in loader.get_available_session_codes(YEAR, GP))

ok = True
for label, status, out in results:
    print(f"[{status}] {label}  ->  {out}")
    if status == "FAIL" or out is False:
        ok = False

print("\nALL PASS" if ok else "\nSOME FAILED")
