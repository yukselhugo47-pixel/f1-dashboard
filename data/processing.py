"""
Feature-specific data transforms. Every function takes an already-loaded
FastF1 Session (see data.loader.get_session) and returns plain
pandas/numpy structures ready to hand to a plotly chart or a Streamlit
widget. Kept separate from app/ so the Streamlit layer stays presentation-only.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parent.parent
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd
from fastf1 import utils

# Track status codes -> human label (per FastF1 / F1 live timing spec)
TRACK_STATUS_LABELS = {
    "1": "Piste dégagée",
    "2": "Drapeau jaune",
    "3": "Drapeau jaune double",
    "4": "Safety Car",
    "5": "Drapeau rouge",
    "6": "Virtual Safety Car",
    "7": "Fin VSC",
}


def _laptime_seconds(series: pd.Series) -> pd.Series:
    return series.dt.total_seconds()


def get_driver_abbreviations(session) -> list[str]:
    laps = session.laps
    if laps is None or laps.empty:
        return list(session.results["Abbreviation"].dropna())
    order = laps.groupby("Driver")["LapNumber"].max().sort_values(ascending=False)
    return list(order.index)


def is_results_final(session) -> bool:
    """False while official classification isn't populated yet - typically
    because the session is still live. Used to fall back to a provisional,
    lap-derived running order instead of an empty/partial results table."""
    res = session.results
    if res is None or res.empty or "Position" not in res.columns:
        return False
    return res["Position"].notna().sum() >= max(1, len(res) // 2)


STATUS_LAP_TEMPLATES = {"fr": "Tour {n}", "en": "Lap {n}"}


def get_live_classification(session, lang: str = "fr") -> pd.DataFrame:
    """Provisional running order built from each driver's latest lap,
    used while a session is in progress and official results aren't final."""
    laps = session.laps
    if laps is None or laps.empty or "Position" not in laps.columns:
        return pd.DataFrame()
    latest = laps.sort_values("LapNumber").groupby("Driver", as_index=False).tail(1)
    latest = latest.dropna(subset=["Position"]).sort_values("Position")
    if latest.empty:
        return pd.DataFrame()
    status_template = STATUS_LAP_TEMPLATES.get(lang, STATUS_LAP_TEMPLATES["fr"])
    rows = []
    for _, lap in latest.iterrows():
        rows.append({
            "Position": int(lap["Position"]),
            "Abbreviation": lap["Driver"],
            "FullName": lap["Driver"],
            "TeamName": lap.get("Team", "?"),
            "GridPosition": np.nan,
            "Time": pd.NaT,
            "Status": status_template.format(n=int(lap["LapNumber"])),
            "Points": np.nan,
        })
    return pd.DataFrame(rows)


def get_effective_results(session, lang: str = "fr") -> pd.DataFrame:
    """Official results if final, otherwise a provisional live classification,
    otherwise whatever official results exist as a last resort."""
    if is_results_final(session):
        return session.results.copy()
    live = get_live_classification(session, lang=lang)
    if not live.empty:
        return live
    return session.results.copy()


def get_results_table(session, lang: str = "fr") -> pd.DataFrame:
    res = get_effective_results(session, lang=lang)
    cols = [c for c in ["Position", "ClassifiedPosition", "GridPosition", "Abbreviation",
                         "FullName", "TeamName", "Time", "Status", "Points"] if c in res.columns]
    out = res[cols].copy()
    if "Time" in out.columns:
        out["Time"] = out["Time"].apply(_fmt_gap)
    return out.reset_index(drop=True)


def _fmt_gap(val) -> str:
    if pd.isna(val):
        return "-"
    if isinstance(val, pd.Timedelta):
        total = val.total_seconds()
        if total <= 0:
            return "-"
        return f"+{total:,.3f}s"
    return str(val)


def get_race_summary(session) -> dict:
    """Podium, pole, fastest lap, safety car periods, weather blurb."""
    results = get_effective_results(session)
    summary: dict = {"is_provisional": not is_results_final(session)}

    if results.empty or "Position" not in results.columns or results["Position"].isna().all():
        summary["podium"] = []
        summary["safety_car_periods"] = get_safety_car_periods(session)
        return summary

    podium = results.sort_values("Position").head(3)
    summary["podium"] = [
        {
            "position": int(row["Position"]) if not pd.isna(row["Position"]) else None,
            "driver": row.get("Abbreviation", "?"),
            "name": row.get("FullName", row.get("Abbreviation", "?")),
            "team": row.get("TeamName", "?"),
        }
        for _, row in podium.iterrows()
    ]

    if "GridPosition" in results.columns and results["GridPosition"].notna().any():
        pole_row = results.sort_values("GridPosition").iloc[0] if not results.empty else None
        if pole_row is not None:
            summary["pole"] = {
                "driver": pole_row.get("Abbreviation", "?"),
                "team": pole_row.get("TeamName", "?"),
            }

    laps = session.laps
    if laps is not None and not laps.empty and laps["LapTime"].notna().any():
        fastest = laps.loc[laps["LapTime"].idxmin()]
        summary["fastest_lap"] = {
            "driver": fastest["Driver"],
            "time": str(fastest["LapTime"])[10:] if pd.notna(fastest["LapTime"]) else "-",
            "lap": int(fastest["LapNumber"]) if pd.notna(fastest["LapNumber"]) else None,
        }

    summary["safety_car_periods"] = get_safety_car_periods(session)

    try:
        weather = session.weather_data
        if weather is not None and not weather.empty:
            summary["weather"] = {
                "air_temp": round(weather["AirTemp"].mean(), 1),
                "track_temp": round(weather["TrackTemp"].mean(), 1),
                "rainfall": bool(weather["Rainfall"].any()),
                "humidity": round(weather["Humidity"].mean(), 1),
            }
    except Exception:
        pass

    return summary


def get_safety_car_periods(session) -> list[dict]:
    """Contiguous SC/VSC windows derived from track status changes."""
    try:
        ts = session.track_status
    except Exception:
        return []
    if ts is None or ts.empty:
        return []

    periods = []
    active_code = None
    start_time = None
    for _, row in ts.iterrows():
        code = str(row["Status"])
        if code in ("4", "6") and active_code is None:
            active_code = code
            start_time = row["Time"]
        elif code not in ("4", "6") and active_code is not None:
            periods.append({
                "type": "Safety Car" if active_code == "4" else "Virtual Safety Car",
                "start": start_time,
                "end": row["Time"],
            })
            active_code = None
    return periods


def get_lap_times_df(session, drivers: list[str] | None = None) -> pd.DataFrame:
    laps = session.laps.copy()
    if drivers:
        laps = laps[laps["Driver"].isin(drivers)]
    laps = laps[laps["LapTime"].notna()].copy()
    laps["LapTimeSeconds"] = _laptime_seconds(laps["LapTime"])
    for sec in ["Sector1Time", "Sector2Time", "Sector3Time"]:
        if sec in laps.columns:
            laps[sec + "Seconds"] = _laptime_seconds(laps[sec])
    return laps


def get_cumulative_delta(session, drv1: str, drv2: str) -> pd.DataFrame:
    """Cumulative time delta drv2 - drv1 across drv1's fastest-lap reference."""
    laps = session.laps
    lap1 = laps.pick_drivers(drv1).pick_fastest()
    lap2 = laps.pick_drivers(drv2).pick_fastest()
    if lap1 is None or lap2 is None:
        return pd.DataFrame()
    delta, ref_tel, _ = utils.delta_time(lap1, lap2)
    out = pd.DataFrame({
        "Distance": ref_tel["Distance"],
        "Delta": delta,
    })
    return out


def get_sector_comparison(session, drivers: list[str]) -> pd.DataFrame:
    laps = get_lap_times_df(session, drivers)
    rows = []
    for drv in drivers:
        d = laps[laps["Driver"] == drv]
        if d.empty:
            continue
        rows.append({
            "Driver": drv,
            "Sector 1": d["Sector1TimeSeconds"].min() if "Sector1TimeSeconds" in d else np.nan,
            "Sector 2": d["Sector2TimeSeconds"].min() if "Sector2TimeSeconds" in d else np.nan,
            "Sector 3": d["Sector3TimeSeconds"].min() if "Sector3TimeSeconds" in d else np.nan,
        })
    return pd.DataFrame(rows)


def get_fastest_lap_telemetry(session, driver: str) -> pd.DataFrame | None:
    lap = session.laps.pick_drivers(driver).pick_fastest()
    if lap is None or pd.isna(lap["LapTime"]):
        return None
    tel = lap.get_telemetry()
    return tel


def get_lap_telemetry(session, driver: str, lap_number: int) -> pd.DataFrame | None:
    laps = session.laps.pick_drivers(driver)
    lap_row = laps[laps["LapNumber"] == lap_number]
    if lap_row.empty:
        return None
    lap = lap_row.iloc[0]
    return lap.get_telemetry()


def get_driver_laps_numbers(session, driver: str) -> list[int]:
    laps = session.laps.pick_drivers(driver)
    laps = laps[laps["LapTime"].notna()]
    return sorted(int(n) for n in laps["LapNumber"].unique())


def get_tire_stints(session) -> pd.DataFrame:
    laps = session.laps
    stints = (
        laps.groupby(["Driver", "Stint", "Compound"])
        .agg(StartLap=("LapNumber", "min"), EndLap=("LapNumber", "max"), Laps=("LapNumber", "count"))
        .reset_index()
        .sort_values(["Driver", "StartLap"])
    )
    return stints


def get_stint_degradation(session) -> pd.DataFrame:
    """Linear regression slope (s/lap) of lap time vs tyre life, per stint."""
    laps = get_lap_times_df(session)
    laps = laps[laps["IsAccurate"]] if "IsAccurate" in laps.columns else laps
    rows = []
    for (drv, stint), grp in laps.groupby(["Driver", "Stint"]):
        grp = grp.dropna(subset=["TyreLife", "LapTimeSeconds"])
        if len(grp) < 3:
            continue
        x = grp["TyreLife"].to_numpy(dtype=float)
        y = grp["LapTimeSeconds"].to_numpy(dtype=float)
        try:
            slope, intercept = np.polyfit(x, y, 1)
        except Exception:
            continue
        rows.append({
            "Driver": drv,
            "Stint": int(stint),
            "Compound": grp["Compound"].iloc[0],
            "DegradationSlope": slope,
            "Laps": len(grp),
            "AvgLapTime": y.mean(),
        })
    return pd.DataFrame(rows)


def get_position_by_lap(session) -> pd.DataFrame:
    laps = session.laps
    df = laps[["Driver", "LapNumber", "Position"]].dropna(subset=["Position"]).copy()
    df["Position"] = df["Position"].astype(int)
    return df


def get_degradation_heatmap(session) -> pd.DataFrame:
    """Driver x LapNumber matrix of lap time delta vs that driver's own median accurate lap."""
    laps = get_lap_times_df(session)
    if "IsAccurate" in laps.columns:
        accurate = laps[laps["IsAccurate"]]
    else:
        accurate = laps
    medians = accurate.groupby("Driver")["LapTimeSeconds"].median()
    laps = laps.copy()
    laps["DeltaToMedian"] = laps.apply(
        lambda r: r["LapTimeSeconds"] - medians.get(r["Driver"], np.nan), axis=1
    )
    return laps[["Driver", "LapNumber", "DeltaToMedian", "Compound", "TyreLife"]]


def get_consistency_ranking(session) -> pd.DataFrame:
    """Std dev of lap times per driver, excluding SC/VSC laps and pit in/out laps."""
    laps = get_lap_times_df(session)
    if "TrackStatus" in laps.columns:
        clean = laps[~laps["TrackStatus"].astype(str).str.contains("4|6|5|2")]
    else:
        clean = laps
    if "PitInTime" in laps.columns:
        clean = clean[clean["PitInTime"].isna() & clean["PitOutTime"].isna()]
    stats = (
        clean.groupby("Driver")["LapTimeSeconds"]
        .agg(["std", "mean", "count"])
        .rename(columns={"std": "StdDev", "mean": "MeanLapTime", "count": "CleanLaps"})
        .dropna()
        .sort_values("StdDev")
        .reset_index()
    )
    return stats


def get_quali_vs_race(quali_session, race_session) -> pd.DataFrame:
    q_res = get_effective_results(quali_session)[["Abbreviation", "Position"]].rename(columns={"Position": "QualiPosition"})
    r_res = get_effective_results(race_session)
    if "GridPosition" not in r_res.columns:
        r_res = r_res.assign(GridPosition=np.nan)
    r_res = r_res[["Abbreviation", "Position", "GridPosition"]].rename(columns={"Position": "RacePosition"})
    merged = pd.merge(q_res, r_res, on="Abbreviation", how="inner")
    merged["PositionsGained"] = merged["QualiPosition"] - merged["RacePosition"]

    race_laps = get_lap_times_df(race_session)
    if "IsAccurate" in race_laps.columns:
        race_laps = race_laps[race_laps["IsAccurate"]]
    pace = race_laps.groupby("Driver")["LapTimeSeconds"].median().rename("MedianRaceLapTime")
    merged = merged.merge(pace, left_on="Abbreviation", right_index=True, how="left")
    merged = merged.sort_values("RacePosition")
    return merged
