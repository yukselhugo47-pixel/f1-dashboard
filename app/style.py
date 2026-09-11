
import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parent.parent
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Titillium+Web:wght@300;400;600;700&display=swap');

:root {
    --bg: #0A0A0C;
    --bg-card: #141417;
    --bg-card-alt: #1A1A1E;
    --red: #E10600;
    --red-dim: #8C0400;
    --grey: #9BA1A6;
    --grey-dim: #848A93;
    --text: #F2F2F2;
    --grid: #2A2A2E;
}

html, body, [class*="css"] {
    font-family: 'Titillium Web', 'Segoe UI', sans-serif !important;
}

.stApp {
    background: radial-gradient(circle at 20% 0%, #131316 0%, #0A0A0C 45%, #08080a 100%) !important;
    color: var(--text);
}

#MainMenu, footer, header[data-testid="stHeader"] {
    background: transparent;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d10 0%, #08080a 100%);
    border-right: 1px solid var(--grid);
}
section[data-testid="stSidebar"] * {
    font-family: 'Titillium Web', sans-serif;
}
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
    font-family: 'Oswald', sans-serif;
    letter-spacing: 0.03em;
    color: var(--text);
}

h1, h2, h3 {
    font-family: 'Oswald', sans-serif !important;
    letter-spacing: 0.02em;
    color: var(--text) !important;
}

/* Bordered containers -> "cards" */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--bg-card);
    border: 1px solid var(--grid) !important;
    border-radius: 10px;
    padding: 4px 2px;
    box-shadow: 0 2px 18px rgba(0,0,0,0.35);
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(225,6,0,0.45) !important;
    box-shadow: 0 4px 24px rgba(225,6,0,0.08);
}

/* Header banner */
.f1-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 18px;
    background: linear-gradient(120deg, #141417 0%, #1c0d0d 100%);
    border: 1px solid var(--grid);
    border-radius: 12px;
    padding: 22px 28px;
    margin-bottom: 22px;
    box-shadow: 0 4px 28px rgba(0,0,0,0.4), inset 0 -3px 0 0 var(--red);
}
.f1-header-title { display: flex; align-items: center; gap: 14px; }
.f1-logo {
    display: inline-flex;
    width: 40px;
    height: 40px;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    background: rgba(225,6,0,0.12);
    filter: drop-shadow(0 0 8px rgba(225,6,0,0.35));
    flex-shrink: 0;
}
.f1-logo svg { width: 22px; height: 22px; stroke: var(--red); }
.f1-title {
    margin: 0;
    font-family: 'Oswald', sans-serif;
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--text);
    line-height: 1.1;
}
.f1-title .accent { color: var(--red); }
.f1-subtitle {
    font-size: 14px;
    color: var(--grey);
    margin-top: 2px;
    letter-spacing: 0.02em;
}
.f1-header-info { display: flex; gap: 26px; flex-wrap: wrap; }
.info-chip { display: flex; flex-direction: column; min-width: 110px; }
.info-chip .label {
    font-size: 10.5px;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: var(--grey-dim);
    font-weight: 600;
}
.info-chip .value {
    font-size: 15.5px;
    font-weight: 600;
    color: var(--text);
    font-family: 'Oswald', sans-serif;
}

/* Section title with red tick marker (not a border - a distinct inline mark) */
.section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'Oswald', sans-serif;
    font-size: 19px;
    font-weight: 600;
    letter-spacing: 0.03em;
    color: var(--text);
    text-transform: uppercase;
    margin: 6px 0 14px 0;
}
.section-title::before {
    content: '';
    display: inline-block;
    width: 8px;
    height: 8px;
    background: var(--red);
    border-radius: 2px;
    flex-shrink: 0;
}

/* Podium cards - accent set per-card via the --accent custom property, kept
   as an inset shadow (not a border) to match the header/section-title pattern */
.podium-card {
    border-radius: 10px;
    padding: 16px 14px;
    text-align: center;
    background: var(--bg-card-alt);
    border: 1px solid var(--grid);
    box-shadow: inset 0 -3px 0 0 var(--accent, var(--grid));
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.podium-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(225,6,0,0.15), inset 0 -3px 0 0 var(--accent, var(--grid));
}
.podium-rank {
    font-family: 'Oswald', sans-serif;
    font-size: 34px;
    font-weight: 700;
    line-height: 1;
}
.podium-photo {
    display: block;
    width: 64px;
    height: 64px;
    border-radius: 50%;
    object-fit: cover;
    object-position: top center;
    background: var(--bg-card);
    border: 2px solid var(--grid);
    margin: 8px auto 0 auto;
}
.podium-driver { font-size: 17px; font-weight: 700; margin-top: 8px; font-family: 'Oswald', sans-serif; }
.podium-team {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12.5px;
    color: var(--grey);
    margin-top: 4px;
}

/* Metric-like stat block */
.stat-block { text-align: center; padding: 6px 0; }
.stat-value { font-family: 'Oswald', sans-serif; font-size: 24px; font-weight: 700; color: var(--text); }
.stat-label { font-size: 11px; color: var(--grey-dim); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px; }

/* Tabs */
button[data-baseweb="tab"] {
    font-family: 'Oswald', sans-serif;
    font-weight: 500;
    letter-spacing: 0.02em;
    color: var(--grey) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--text) !important;
}
div[data-baseweb="tab-highlight"] {
    background-color: var(--red) !important;
}
div[data-baseweb="tab-border"] { background-color: var(--grid) !important; }

/* Outer category tabs (Course/Pilote/Stratégie) read as section nav: bigger,
   bolder, with breathing room above the inner feature tabs they contain. */
div[data-testid="stTabs"] > div[data-baseweb="tab-list"] button[data-baseweb="tab"] {
    font-size: 16px;
    padding: 10px 18px;
}
/* Inner feature tabs, nested one stTabs deep inside the category tabs:
   smaller and tighter, so the two levels read as a clear hierarchy rather
   than two identical, confusing rows. */
div[data-testid="stTabs"] div[data-testid="stTabs"] > div[data-baseweb="tab-list"] button[data-baseweb="tab"] {
    font-size: 13.5px;
    padding: 7px 14px;
    font-weight: 400;
}
div[data-testid="stTabs"] div[data-testid="stTabs"] {
    margin-top: 4px;
}

/* Dataframes */
[data-testid="stDataFrame"] { border: 1px solid var(--grid); border-radius: 8px; overflow: hidden; }

/* Metrics */
div[data-testid="stMetric"] {
    background: var(--bg-card-alt);
    border: 1px solid var(--grid);
    border-radius: 10px;
    padding: 10px 14px;
}
div[data-testid="stMetricLabel"] { color: var(--grey); }

/* Badges for SC / VSC periods */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11.5px;
    font-weight: 600;
    letter-spacing: 0.03em;
    margin: 2px 4px 2px 0;
}
.badge-sc { background: rgba(225,6,0,0.15); color: #ff6b60; border: 1px solid rgba(225,6,0,0.4); }
.badge-vsc { background: rgba(255,193,7,0.12); color: #ffcf50; border: 1px solid rgba(255,193,7,0.35); }

hr { border-color: var(--grid) !important; }

/* Live indicator */
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'Oswald', sans-serif;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.06em;
    color: var(--red);
}
.live-dot {
    display: inline-block;
    width: 9px;
    height: 9px;
    vertical-align: middle;
    border-radius: 50%;
    background: var(--red);
    box-shadow: 0 0 0 rgba(225,6,0,0.55);
    animation: live-pulse 1.6s infinite;
}
@keyframes live-pulse {
    0%   { box-shadow: 0 0 0 0 rgba(225,6,0,0.55); }
    70%  { box-shadow: 0 0 0 8px rgba(225,6,0,0); }
    100% { box-shadow: 0 0 0 0 rgba(225,6,0,0); }
}

/* Browser surfaces carry the design too */
::selection { background: var(--red); color: #fff; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--grid); border-radius: 6px; }
::-webkit-scrollbar-thumb:hover { background: var(--red-dim); }
*:focus-visible { outline: 2px solid var(--red) !important; outline-offset: 2px; }

.stat-value, .podium-rank, .info-chip .value, [data-testid="stMetricValue"] {
    font-variant-numeric: tabular-nums;
}

/* AI commentary card */
.ai-commentary {
    background: linear-gradient(120deg, rgba(225,6,0,0.07), rgba(225,6,0,0.015));
    border: 1px solid rgba(225,6,0,0.22);
    border-radius: 10px;
    padding: 12px 16px;
    margin: 4px 0 16px 0;
}
.ai-commentary-label {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'Oswald', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--red);
    margin-bottom: 6px;
}
.ai-commentary-label svg { width: 14px; height: 14px; stroke: var(--red); flex-shrink: 0; }
.ai-commentary-text {
    font-size: 13.5px;
    line-height: 1.55;
    color: var(--text);
}

/* Driver badge: headshot + name + team logo, wherever a driver is picked */
.driver-badge {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 0 14px 0;
}
.driver-badge-photo {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    object-fit: cover;
    background: var(--bg-card-alt);
    border: 2px solid var(--grid);
    flex-shrink: 0;
}
.driver-badge-photo-placeholder { background: var(--bg-card-alt); }
.driver-badge-name {
    font-family: 'Oswald', sans-serif;
    font-weight: 700;
    font-size: 15px;
    color: var(--text);
    line-height: 1.2;
}
.driver-badge-team {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--grey);
    margin-top: 3px;
}
.driver-badge-logo { height: 15px; width: auto; }

/* Team car image */
.team-car-image {
    width: 100%;
    max-width: 420px;
    height: auto;
    display: block;
    margin: 6px auto 10px auto;
    filter: drop-shadow(0 6px 16px rgba(0,0,0,0.45));
}

/* Team logo inline with text (podium cards, etc.) */
.team-logo-inline { height: 16px; width: auto; vertical-align: middle; margin-right: 5px; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)
