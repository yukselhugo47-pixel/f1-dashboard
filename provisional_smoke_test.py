"""
Validates the provisional-classification fallback (used when a live session's
official results aren't populated yet) by artificially blanking out the
Position column of a real, fully-loaded session's results - simulating what
session.results looks like mid-race - and checking the derived views still
work sensibly.
"""
import fastf1
import numpy as np

from data.loader import CACHE_DIR
fastf1.Cache.enable_cache(str(CACHE_DIR))

from data import processing as proc

YEAR, GP = 2024, "Abu Dhabi Grand Prix"

race = fastf1.get_session(YEAR, GP, "R")
race.load(laps=True, telemetry=False, weather=True, messages=True)
quali = fastf1.get_session(YEAR, GP, "Q")
quali.load(laps=True, telemetry=False, weather=False, messages=False)

# Simulate "race still in progress": blank the official classification.
race.results["Position"] = np.nan
race.results["GridPosition"] = np.nan if "GridPosition" in race.results.columns else race.results.get("GridPosition")

results = []


def check(label, fn):
    try:
        out = fn()
        results.append((label, "OK", out))
    except Exception as e:
        import traceback
        results.append((label, "FAIL", traceback.format_exc()[-800:]))


check("is_results_final == False", lambda: proc.is_results_final(race) is False)
check("get_live_classification non-empty", lambda: not proc.get_live_classification(race).empty)
check("get_live_classification sorted by Position", lambda:
      list(proc.get_live_classification(race)["Position"]) == sorted(proc.get_live_classification(race)["Position"]))
check("get_effective_results non-empty", lambda: not proc.get_effective_results(race).empty)
check("get_results_table non-empty", lambda: not proc.get_results_table(race).empty)

summary = None


def summary_check():
    global summary
    summary = proc.get_race_summary(race)
    return summary["is_provisional"] is True and len(summary["podium"]) == 3


check("get_race_summary: provisional + 3-car podium", summary_check)
check("pole absent when GridPosition all-NaN", lambda: "pole" not in summary)
check("quali_vs_race works with provisional race results", lambda: not proc.get_quali_vs_race(quali, race).empty)

ok = True
for label, status, out in results:
    print(f"[{status}] {label}  ->  {out if status == 'OK' else ''}")
    if status == "FAIL":
        print(out)
        ok = False
    elif status == "OK" and out is False:
        ok = False

if summary:
    print("\npodium sample:", summary.get("podium"))

print("\nALL PASS" if ok else "\nSOME FAILED")
