import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from app import i18n
from app.i18n import t
from app.style import inject_css
from app.components.header import render_header
from app.components.overview import render_overview
from app.components.driver_comparison import render_driver_comparison
from app.components.track_map import render_track_map
from app.components.tire_strategy import render_tire_strategy
from app.components.race_chart import render_race_chart
from app.components.telemetry import render_telemetry
from app.components.degradation_heatmap import render_degradation_heatmap
from app.components.quali_vs_race import render_quali_vs_race
from app.components.consistency import render_consistency
from data import loader, processing as proc

qp = st.query_params
qp_lang = qp.get("lang")
if qp_lang in ("fr", "en"):
    i18n.set_lang(qp_lang)

st.set_page_config(page_title=t("page.title"), page_icon=":material/sports_motorsports:", layout="wide")
inject_css()

DEFAULT_YEAR = 2024
DEFAULT_GP = "Abu Dhabi Grand Prix"
DEFAULT_SESSION = "Course"

SESSION_CODES = {
    "Course": "R",
    "Qualifications": "Q",
    "Sprint": "S",
    "Sprint - Qualifications": "SQ",
    "Essais libres 1": "FP1",
    "Essais libres 2": "FP2",
    "Essais libres 3": "FP3",
}
CODE_TO_LABEL = {v: k for k, v in SESSION_CODES.items()}

# Internal keys (stable, used in query params) -> translated display label.
CATEGORY_NAMES = ["race", "driver", "strategy"]
CATEGORY_ICONS = {"race": ":material/flag:", "driver": ":material/person:", "strategy": ":material/route:"}
CATEGORY_I18N_KEYS = {"race": "cat.race", "driver": "cat.driver", "strategy": "cat.strategy"}


def safe_render(fn, *args):
    try:
        fn(*args)
    except Exception as exc:  # noqa: BLE001
        st.error(t("error.tab_render"))
        with st.expander(t("error.technical_details")):
            st.code(f"{type(exc).__name__}: {exc}")


with st.sidebar:
    st.markdown(f"## {t('sidebar.title')}")
    st.caption(t("sidebar.tagline"))

    lang_options = {"fr": "FR", "en": "EN"}
    current_lang = i18n.get_lang()
    chosen = st.segmented_control(
        t("sidebar.lang_label"),
        options=list(lang_options.keys()),
        format_func=lambda code: lang_options[code],
        default=current_lang,
        required=True,
        label_visibility="collapsed",
    )
    if chosen and chosen != current_lang:
        i18n.set_lang(chosen)
        qp["lang"] = chosen
        st.rerun()
    qp["lang"] = current_lang

    st.divider()

    years = list(range(2026, 2017, -1))
    try:
        qp_year = int(qp.get("year", DEFAULT_YEAR))
    except (TypeError, ValueError):
        qp_year = DEFAULT_YEAR
    default_year = qp_year if qp_year in years else DEFAULT_YEAR
    year = st.selectbox(t("sidebar.year"), years, index=years.index(default_year) if default_year in years else 0)

    try:
        gp_names = loader.get_selectable_event_names(year)
    except Exception as exc:
        st.error(t("sidebar.calendar_error", year=year, exc=exc))
        st.stop()

    if not gp_names:
        st.warning(t("sidebar.no_gp"))
        st.stop()

    qp_gp = qp.get("gp")
    if qp_gp in gp_names:
        default_gp_index = gp_names.index(qp_gp)
    elif DEFAULT_GP in gp_names:
        default_gp_index = gp_names.index(DEFAULT_GP)
    else:
        default_gp_index = len(gp_names) - 1
    gp = st.selectbox(t("sidebar.gp"), gp_names, index=default_gp_index)

    try:
        available_codes = loader.get_available_session_codes(year, gp)
    except Exception:
        available_codes = list(SESSION_CODES.values())

    session_names = [CODE_TO_LABEL[c] for c in available_codes if c in CODE_TO_LABEL]
    if not session_names:
        st.info(t("sidebar.weekend_not_started", gp=gp))
        st.stop()

    qp_session_label = CODE_TO_LABEL.get(qp.get("session"))
    if qp_session_label in session_names:
        default_session_index = session_names.index(qp_session_label)
    elif DEFAULT_SESSION in session_names and gp == DEFAULT_GP and year == DEFAULT_YEAR:
        default_session_index = session_names.index(DEFAULT_SESSION)
    else:
        default_session_index = len(session_names) - 1  # most recently started session
    session_name = st.selectbox(t("sidebar.session"), session_names, index=default_session_index)
    session_code = SESSION_CODES[session_name]

    is_live = loader.is_session_live(year, gp, session_code)

    st.divider()
    if is_live:
        st.markdown(
            f'<span class="live-badge"><span class="live-dot"></span>{t("sidebar.live_badge")}</span>',
            unsafe_allow_html=True,
        )
        st.caption(t("sidebar.live_caption"))
        auto_refresh = st.toggle(t("sidebar.auto_refresh"), value=True)
        refresh_interval = st.select_slider(
            t("sidebar.interval"), options=[15, 20, 30, 45, 60], value=20, format_func=lambda s: f"{s}s",
        )
        if auto_refresh:
            st_autorefresh(interval=refresh_interval * 1000, key="live_autorefresh")
        st.session_state.setdefault("force_refresh_token", 0)
        if st.button(t("sidebar.refresh_now"), icon=":material/refresh:", width="stretch"):
            st.session_state["force_refresh_token"] += 1
            st.rerun()
    else:
        st.caption(t("sidebar.help_caption"))
    st.divider()
    st.caption(t("sidebar.default_race_caption"))
    st.caption(t("sidebar.share_caption"))

qp["year"] = str(year)
qp["gp"] = gp
qp["session"] = session_code

try:
    force_token = st.session_state.get("force_refresh_token", 0)
    session = loader.get_session(year, gp, session_code, force_token=force_token)
except Exception as exc:
    st.error(t("error.session_load", session_name=session_name, gp=gp, year=year))
    with st.expander(t("error.technical_details")):
        st.code(f"{type(exc).__name__}: {exc}")
    st.stop()

try:
    summary = proc.get_race_summary(session)
except Exception:
    summary = {}
render_header(session, summary, is_live=is_live)

# Restore the last-focused driver (shared across driver-centric tabs) from the
# shared link, if present, before any tab reads/seeds it.
qp_driver = qp.get("driver")
if qp_driver and "focus_driver" not in st.session_state:
    st.session_state["focus_driver"] = qp_driver

category_labels = [f"{CATEGORY_ICONS[c]} {t(CATEGORY_I18N_KEYS[c])}" for c in CATEGORY_NAMES]
qp_cat = qp.get("cat")
default_cat_label = (
    f"{CATEGORY_ICONS[qp_cat]} {t(CATEGORY_I18N_KEYS[qp_cat])}" if qp_cat in CATEGORY_NAMES else None
)
cat_tabs = st.tabs(category_labels, default=default_cat_label, on_change="rerun")

active_category = CATEGORY_NAMES[0]
for name, tab in zip(CATEGORY_NAMES, cat_tabs):
    if tab.open:
        active_category = name
qp["cat"] = active_category

with cat_tabs[0]:  # Course / Race
    if cat_tabs[0].open:
        sub = st.tabs([
            f":material/trophy: {t('tab.overview')}",
            f":material/show_chart: {t('tab.positions')}",
            f":material/track_changes: {t('tab.quali_vs_race')}",
        ], on_change="rerun")
        with sub[0]:
            if sub[0].open:
                safe_render(render_overview, session)
        with sub[1]:
            if sub[1].open:
                safe_render(render_race_chart, session)
        with sub[2]:
            if sub[2].open:
                safe_render(render_quali_vs_race, year, gp, session)

with cat_tabs[1]:  # Pilote / Driver
    if cat_tabs[1].open:
        sub = st.tabs([
            f":material/compare_arrows: {t('tab.comparison')}",
            f":material/sensors: {t('tab.telemetry')}",
            f":material/straighten: {t('tab.consistency')}",
        ], on_change="rerun")
        with sub[0]:
            if sub[0].open:
                safe_render(render_driver_comparison, session)
        with sub[1]:
            if sub[1].open:
                safe_render(render_telemetry, session)
        with sub[2]:
            if sub[2].open:
                safe_render(render_consistency, session)

with cat_tabs[2]:  # Stratégie / Strategy
    if cat_tabs[2].open:
        sub = st.tabs([
            f":material/map: {t('tab.track_map')}",
            f":material/tire_repair: {t('tab.tire_strategy')}",
            f":material/local_fire_department: {t('tab.degradation')}",
        ], on_change="rerun")
        with sub[0]:
            if sub[0].open:
                safe_render(render_track_map, session)
        with sub[1]:
            if sub[1].open:
                safe_render(render_tire_strategy, session)
        with sub[2]:
            if sub[2].open:
                safe_render(render_degradation_heatmap, session)

if st.session_state.get("focus_driver"):
    qp["driver"] = st.session_state["focus_driver"]

st.divider()
st.caption(t("footer.caption"))
