
import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from app import ai_commentary, media, theme
from app.i18n import t, get_lang
from data import loader, processing as proc


def _channels():
    return [
        ("Speed", t("tel.channel_speed")),
        ("Throttle", t("tel.channel_throttle")),
        ("Brake", t("tel.channel_brake")),
        ("nGear", t("tel.channel_gear")),
        ("RPM", t("tel.channel_rpm")),
    ]


def render_telemetry(session):
    st.markdown(theme.section_title(t("tel.title")), unsafe_allow_html=True)
    with st.spinner(t("map.loading_telemetry")):
        loader.ensure_telemetry(session)

    drivers = proc.get_driver_abbreviations(session)
    if len(drivers) < 2:
        st.warning(t("tel.not_enough_drivers"))
        return

    focus = st.session_state.get("focus_driver")
    default_idx = drivers.index(focus) if focus in drivers else 0

    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    drv1 = c1.selectbox(t("tel.driver_a"), drivers, index=default_idx, key="tel_drv1")
    st.session_state["focus_driver"] = drv1
    remaining = [d for d in drivers if d != drv1]
    drv2 = c2.selectbox(t("tel.driver_b"), remaining, index=0, key="tel_drv2")

    b1, b2 = st.columns(2)
    b1.markdown(media.driver_badge_html(session, drv1), unsafe_allow_html=True)
    b2.markdown(media.driver_badge_html(session, drv2), unsafe_allow_html=True)

    laps1 = proc.get_driver_laps_numbers(session, drv1)
    laps2 = proc.get_driver_laps_numbers(session, drv2)
    if not laps1 or not laps2:
        st.info(t("tel.no_laps"))
        return

    lap1 = c3.selectbox(t("tel.lap_for", driver=drv1), laps1, index=len(laps1) - 1, key="tel_lap1")
    lap2 = c4.selectbox(t("tel.lap_for", driver=drv2), laps2, index=len(laps2) - 1, key="tel_lap2")

    tel1 = proc.get_lap_telemetry(session, drv1, lap1)
    tel2 = proc.get_lap_telemetry(session, drv2, lap2)
    if tel1 is None or tel2 is None or tel1.empty or tel2.empty:
        st.info(t("tel.no_telemetry"))
        return

    color1 = theme.driver_color(session, drv1, 0)
    color2 = theme.driver_color(session, drv2, 1)

    max1 = tel1["Speed"].max() if "Speed" in tel1.columns else None
    max2 = tel2["Speed"].max() if "Speed" in tel2.columns else None
    brake1 = int((tel1["Brake"] > 0).sum()) if "Brake" in tel1.columns else None
    brake2 = int((tel2["Brake"] > 0).sum()) if "Brake" in tel2.columns else None
    prompt = (
        f"{drv1} tour {lap1}: vitesse max {max1:.0f} km/h, {brake1} points de mesure sous freinage. "
        f"{drv2} tour {lap2}: vitesse max {max2:.0f} km/h, {brake2} points de mesure sous freinage. "
        "Compare brièvement le style de pilotage (vitesse de pointe, freinage) entre ces deux tours."
    )
    ai_commentary.render_commentary(
        ai_commentary.session_key(session) + ("telemetry", drv1, lap1, drv2, lap2), prompt, get_lang()
    )

    channels = _channels()
    with st.container(border=True):
        fig = make_subplots(
            rows=len(channels), cols=1, shared_xaxes=True, vertical_spacing=0.035,
            subplot_titles=[label for _, label in channels],
        )
        for i, (channel, label) in enumerate(channels, start=1):
            for tel, drv, color in [(tel1, drv1, color1), (tel2, drv2, color2)]:
                if channel not in tel.columns:
                    continue
                fig.add_trace(
                    go.Scatter(
                        x=tel["Distance"], y=tel[channel], mode="lines",
                        line=dict(color=color, width=2),
                        name=t("tel.legend_lap", driver=drv, lap=lap1 if drv == drv1 else lap2),
                        legendgroup=drv, showlegend=(i == 1),
                        hovertemplate="%{y}<extra>" + drv + "</extra>",
                    ),
                    row=i, col=1,
                )
        theme.style_fig(fig, height=980)
        fig.update_layout(legend=dict(orientation="h", y=1.04))
        fig.update_xaxes(title=t("tel.distance_axis"), row=len(channels), col=1)
        for annotation in fig["layout"]["annotations"]:
            annotation["font"] = dict(size=13, family=theme.HEADER_FONT, color=theme.GREY)
        st.plotly_chart(fig, width="stretch")
