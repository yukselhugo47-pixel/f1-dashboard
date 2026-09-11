"""
FastF1 session loading, all wrapped in Streamlit caches so the network/disk
FastF1 cache is only hit once per (year, gp, session) combination per app
process. FastF1's own on-disk cache (.cache/) additionally survives across
app restarts, so a session already viewed once loads instantly next time.

Live sessions (a Grand Prix weekend currently in progress) are handled
separately: caching is bypassed and re-fetched on a short interval instead,
see `is_session_live` / `get_session`.
"""

import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parent.parent
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

import time
from datetime import timedelta
from pathlib import Path

import fastf1
import pandas as pd
import streamlit as st

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

SESSION_LABELS = {
    "Race": "R",
    "Qualifying": "Q",
    "Sprint": "S",
    "Sprint Qualifying": "SQ",
    "Practice 1": "FP1",
    "Practice 2": "FP2",
    "Practice 3": "FP3",
}

# Maps our session codes to the exact session-name strings FastF1 uses in
# the event schedule's Session1..Session5 columns (also covers sprint
# weekends, where the slot order/names differ from a conventional weekend).
SESSION_CODE_TO_SCHEDULE_NAME = {v: k for k, v in SESSION_LABELS.items()}

# How long a session is considered "live" after its scheduled start: generous
# on purpose to absorb delays, red flags and FastF1/F1 API publication lag.
LIVE_WINDOW = timedelta(hours=4)
# How far ahead of race day a not-yet-finished event still shows up in the
# picker, so Friday practice is selectable a couple of days before Sunday.
EVENT_LOOKAHEAD = timedelta(days=3)
# Live data is re-fetched (bypassing all caches) at most this often.
LIVE_REFRESH_SECONDS = 20


@st.cache_data(show_spinner=False, ttl=3600 * 24)
def get_event_schedule(year: int) -> pd.DataFrame:
    schedule = fastf1.get_event_schedule(year, include_testing=False)
    return schedule


@st.cache_data(show_spinner=False, ttl=60)
def get_selectable_event_names(year: int) -> list[str]:
    """Grands Prix for `year` with at least one session already reachable:
    fully past events, plus the current one once its race weekend is close
    (so Friday practice is pickable before Sunday's race has happened)."""
    schedule = get_event_schedule(year)
    now = pd.Timestamp.now()
    mask = (schedule["EventDate"] < now) | ((schedule["EventDate"] - now) <= EVENT_LOOKAHEAD)
    return list(schedule[mask]["EventName"])


def _get_event_row(year: int, gp: str) -> pd.Series | None:
    schedule = get_event_schedule(year)
    matches = schedule[schedule["EventName"] == gp]
    if matches.empty:
        matches = schedule[schedule["EventName"].str.contains(gp, case=False, na=False)]
    return matches.iloc[0] if not matches.empty else None


def _session_start_utc(row: pd.Series, session_code: str) -> pd.Timestamp | None:
    target_name = SESSION_CODE_TO_SCHEDULE_NAME.get(session_code)
    if target_name is None:
        return None
    for i in range(1, 6):
        if row.get(f"Session{i}") == target_name:
            ts = row.get(f"Session{i}DateUtc")
            if pd.notna(ts):
                return pd.Timestamp(ts)
    return None


@st.cache_data(show_spinner=False, ttl=60)
def get_available_session_codes(year: int, gp: str) -> list[str]:
    """Session codes that both exist for this event and have already
    started (chronological order), used to only offer sessions with data."""
    row = _get_event_row(year, gp)
    if row is None:
        return list(SESSION_CODE_TO_SCHEDULE_NAME.keys())
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    codes = []
    for i in range(1, 6):
        name = row.get(f"Session{i}")
        code = SESSION_LABELS.get(name)
        if code is None:
            continue
        ts = row.get(f"Session{i}DateUtc")
        if pd.notna(ts) and pd.Timestamp(ts) <= now:
            codes.append(code)
    return codes


def is_session_live(year: int, gp: str, session_code: str) -> bool:
    """True while `now` falls within a generous window after the session's
    scheduled start. Heuristic only (FastF1 exposes no "session finished"
    flag ahead of loading data), but degrades safely either way: a false
    positive on an old race just means one uncached reload; a false
    negative on a genuinely live session just falls back to normal
    (non-refreshing) loading."""
    row = _get_event_row(year, gp)
    if row is None:
        return False
    start = _session_start_utc(row, session_code)
    if start is None:
        return False
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    return start <= now <= start + LIVE_WINDOW


def get_session_start_local(year: int, gp: str, session_code: str) -> pd.Timestamp | None:
    row = _get_event_row(year, gp)
    if row is None:
        return None
    target_name = SESSION_CODE_TO_SCHEDULE_NAME.get(session_code)
    for i in range(1, 6):
        if row.get(f"Session{i}") == target_name:
            ts = row.get(f"Session{i}Date")
            return pd.Timestamp(ts) if pd.notna(ts) else None
    return None


@st.cache_resource(show_spinner="Chargement des données FastF1 (tours, résultats)...", ttl=3600 * 24)
def _get_session_cached(year: int, gp: str, session_code: str):
    session = fastf1.get_session(year, gp, session_code)
    # Telemetry deliberately excluded here: it's by far the heaviest fetch
    # (car + position data for every driver, every lap) and only 3 of the
    # 9 tabs actually need it. Loading it eagerly for every session view
    # made the app unusable on resource-constrained free hosting (Render's
    # free tier in particular) - see `ensure_telemetry` below, called only
    # by the tabs that need it. FastF1's own docs note that splitting the
    # load can very slightly reduce cross-referenced data corrections
    # versus loading everything in one call; accepted as the right
    # trade-off given the alternative was the app not working at all.
    session.load(laps=True, telemetry=False, weather=True, messages=True)
    return session


@st.cache_resource(show_spinner="🔴 Actualisation des données en direct...", ttl=LIVE_REFRESH_SECONDS + 10)
def _get_session_live(year: int, gp: str, session_code: str, refresh_key: tuple):
    # Cache disabled so every refresh really re-fetches from the F1 API
    # instead of replaying whatever was cached the first time this
    # (year, gp, session) combination was requested.
    with fastf1.Cache.disabled():
        session = fastf1.get_session(year, gp, session_code)
        session.load(laps=True, telemetry=False, weather=True, messages=True)
    return session


def get_session(year: int, gp: str, session_code: str, force_token: int = 0):
    """Load a FastF1 session with laps and results populated (telemetry is
    loaded on demand - see `ensure_telemetry`).

    Historical sessions are cached indefinitely (immutable data, cheap
    disk-cache reloads via FastF1 itself). A session detected as currently
    live is instead re-fetched from the network at most every
    LIVE_REFRESH_SECONDS, bypassing FastF1's own cache so updates during
    the session (new laps, pit stops, ...) actually show up. `force_token`
    lets the UI request an immediate refresh (e.g. a manual "refresh now"
    button) ahead of the next automatic interval.
    """
    if is_session_live(year, gp, session_code):
        bucket = int(time.time() // LIVE_REFRESH_SECONDS)
        return _get_session_live(year, gp, session_code, (bucket, force_token))
    return _get_session_cached(year, gp, session_code)


def ensure_telemetry(session) -> None:
    """Load telemetry (car + position data) into an already-loaded session,
    if it isn't already there. Mutates `session` in place - safe to call
    from every tab that needs telemetry; the second and later calls for the
    same session object are near-instant no-ops."""
    if getattr(session, "_telemetry_ensured", False):
        return
    session.load(laps=False, telemetry=True, weather=False, messages=False)
    session._telemetry_ensured = True


def session_is_loadable(year: int, gp: str, session_code: str) -> tuple[bool, str]:
    try:
        session = fastf1.get_session(year, gp, session_code)
        session.load(laps=False, telemetry=False, weather=False, messages=False)
        return True, ""
    except Exception as exc:  # noqa: BLE001 - surfaced to the UI as-is
        return False, str(exc)
