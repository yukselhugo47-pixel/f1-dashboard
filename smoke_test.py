import sys
import traceback

import fastf1
from data import processing as proc
from data.loader import CACHE_DIR

fastf1.Cache.enable_cache(str(CACHE_DIR))

YEAR, GP = 2024, "Abu Dhabi Grand Prix"

results = {}


def check(name, fn):
    try:
        out = fn()
        results[name] = ("OK", out)
    except Exception as e:
        results[name] = ("FAIL", "".join(traceback.format_exception(type(e), e, e.__traceback__))[-1500:])


print("Loading Race session...")
race = fastf1.get_session(YEAR, GP, "R")
race.load(laps=True, telemetry=True, weather=True, messages=True)
print("Loading Qualifying session...")
quali = fastf1.get_session(YEAR, GP, "Q")
quali.load(laps=True, telemetry=True, weather=False, messages=False)

drivers = proc.get_driver_abbreviations(race)
d1, d2 = drivers[0], drivers[1]
print("drivers sample:", d1, d2)

check("results_table", lambda: proc.get_results_table(race))
check("race_summary", lambda: proc.get_race_summary(race))
check("safety_car_periods", lambda: proc.get_safety_car_periods(race))
check("lap_times_df", lambda: proc.get_lap_times_df(race, [d1, d2]))
check("cumulative_delta", lambda: proc.get_cumulative_delta(race, d1, d2))
check("sector_comparison", lambda: proc.get_sector_comparison(race, [d1, d2]))
check("fastest_lap_telemetry", lambda: proc.get_fastest_lap_telemetry(race, d1))
check("driver_laps_numbers", lambda: proc.get_driver_laps_numbers(race, d1))
lap_nums = proc.get_driver_laps_numbers(race, d1)
check("lap_telemetry", lambda: proc.get_lap_telemetry(race, d1, lap_nums[-1]))
check("tire_stints", lambda: proc.get_tire_stints(race))
check("stint_degradation", lambda: proc.get_stint_degradation(race))
check("position_by_lap", lambda: proc.get_position_by_lap(race))
check("degradation_heatmap", lambda: proc.get_degradation_heatmap(race))
check("consistency_ranking", lambda: proc.get_consistency_ranking(race))
check("quali_vs_race", lambda: proc.get_quali_vs_race(quali, race))

ok = True
for name, (status, out) in results.items():
    if status == "OK":
        shape = getattr(out, "shape", None)
        print(f"[OK]   {name}  shape={shape}")
    else:
        ok = False
        print(f"[FAIL] {name}\n{out}\n")

sys.exit(0 if ok else 1)
