"""
Driver headshots and team logos/car images - all hotlinked directly from
their official sources, never downloaded or redistributed:

- Driver headshots come straight from FastF1's own `HeadshotUrl` column
  (sourced from F1's official media), no guessing involved.
- Team logos/car images come from Formula1.com's public media CDN. FastF1
  doesn't expose these, so the URL is built from a small, explicit
  TeamId -> CDN-slug map covering the current-era grid (2023+ team
  identities). Older/renamed teams (pre-2023 rebrands - Alfa Romeo, Racing
  Point, Toro Rosso, AlphaTauri, Renault, ...) aren't in this map since
  their slugs on the current CDN weren't verified; those are skipped
  silently rather than guessed and risking a broken image.

Every <img> here carries an inline onerror handler that hides it on a
broken/expired link, so a stale URL degrades to "no image", never a
visible broken-image icon.
"""
from __future__ import annotations

TEAM_MEDIA_YEAR = "2025"

TEAM_ID_TO_SLUG = {
    "mclaren": "mclaren",
    "ferrari": "ferrari",
    "mercedes": "mercedes",
    "red_bull": "redbullracing",
    "alpine": "alpine",
    "haas": "haasf1team",
    "aston_martin": "astonmartin",
    "williams": "williams",
    "rb": "racingbulls",
    "sauber": "kicksauber",
}


def team_logo_url(team_id: str | None) -> str | None:
    slug = TEAM_ID_TO_SLUG.get(team_id or "")
    if not slug:
        return None
    return (
        "https://media.formula1.com/image/upload/c_fit,h_128/q_auto/"
        f"common/f1/{TEAM_MEDIA_YEAR}/{slug}/{TEAM_MEDIA_YEAR}{slug}logowhite.webp"
    )


def team_car_url(team_id: str | None) -> str | None:
    slug = TEAM_ID_TO_SLUG.get(team_id or "")
    if not slug:
        return None
    return (
        "https://media.formula1.com/image/upload/c_lfill,w_800/q_auto/"
        f"common/f1/{TEAM_MEDIA_YEAR}/{slug}/{TEAM_MEDIA_YEAR}{slug}carright.webp"
    )


def driver_info(session, driver_abbr: str) -> dict:
    """Headshot URL, full name, team name and team id for one driver
    abbreviation, or an all-None dict if the driver/session has no results
    row (e.g. a practice session with incomplete classification)."""
    empty = {"headshot": None, "name": driver_abbr, "team_name": None, "team_id": None}
    try:
        row = session.results[session.results["Abbreviation"] == driver_abbr]
        if row.empty:
            return empty
        row = row.iloc[0]
        headshot = row.get("HeadshotUrl")
        return {
            "headshot": headshot if isinstance(headshot, str) and headshot.startswith("http") else None,
            "name": row.get("FullName") or driver_abbr,
            "team_name": row.get("TeamName"),
            "team_id": row.get("TeamId"),
        }
    except Exception:
        return empty


def driver_badge_html(session, driver_abbr: str) -> str:
    """Small card: headshot + name + team logo, for wherever a driver is
    picked from a selectbox."""
    info = driver_info(session, driver_abbr)
    logo = team_logo_url(info["team_id"])
    photo_html = (
        f'<img class="driver-badge-photo" src="{info["headshot"]}" '
        f'onerror="this.style.display=\'none\'" alt="">'
        if info["headshot"]
        else '<div class="driver-badge-photo driver-badge-photo-placeholder"></div>'
    )
    logo_html = (
        f'<img class="driver-badge-logo" src="{logo}" onerror="this.style.display=\'none\'" alt="">'
        if logo
        else ""
    )
    team_name = info["team_name"] or ""
    return (
        '<div class="driver-badge">'
        f"{photo_html}"
        '<div class="driver-badge-info">'
        f'<div class="driver-badge-name">{info["name"]}</div>'
        f'<div class="driver-badge-team">{logo_html}<span>{team_name}</span></div>'
        "</div>"
        "</div>"
    )


def team_car_html(session, driver_abbr: str) -> str | None:
    """Wide car image for the driver's team, or None if the team isn't in
    the CDN-slug map (older/renamed teams)."""
    info = driver_info(session, driver_abbr)
    car = team_car_url(info["team_id"])
    if not car:
        return None
    return (
        f'<img class="team-car-image" src="{car}" '
        f'onerror="this.style.display=\'none\'" alt="{info["team_name"] or ""}">'
    )
