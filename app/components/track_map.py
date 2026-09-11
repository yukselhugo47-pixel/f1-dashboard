
import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

import plotly.graph_objects as go
import streamlit as st

from app import ai_commentary, media, theme
from app.i18n import t, get_lang
from data import processing as proc

SPEED_COLORSCALE = [
    [0.0, "#2B2B30"],
    [0.28, "#3671C6"],
    [0.55, "#E10600"],
    [0.8, "#FF8000"],
    [1.0, "#FFD400"],
]


def render_track_map(session):
    st.markdown(theme.section_title(t("map.title")), unsafe_allow_html=True)

    drivers = proc.get_driver_abbreviations(session)
    if not drivers:
        st.warning(t("map.no_laps"))
        return

    focus = st.session_state.get("focus_driver")
    default_idx = drivers.index(focus) if focus in drivers else 0

    c1, c2 = st.columns([1, 3])
    driver = c1.selectbox(t("map.driver"), drivers, index=default_idx, key="map_driver")
    st.session_state["focus_driver"] = driver
    c1.markdown(media.driver_badge_html(session, driver), unsafe_allow_html=True)
    car_html = media.team_car_html(session, driver)
    if car_html:
        c2.markdown(car_html, unsafe_allow_html=True)

    tel = proc.get_fastest_lap_telemetry(session, driver)
    if tel is None or tel.empty or "X" not in tel.columns:
        st.info(t("map.no_position", driver=driver))
        return

    with st.container(border=True):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=tel["X"], y=tel["Y"], mode="lines",
            line=dict(color="#26262b", width=14), hoverinfo="skip", showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=tel["X"], y=tel["Y"], mode="markers",
            marker=dict(
                color=tel["Speed"], colorscale=SPEED_COLORSCALE, size=6,
                colorbar=dict(title=dict(text="km/h", font=dict(color=theme.TEXT)),
                               tickfont=dict(color=theme.TEXT), thickness=14, outlinewidth=0),
            ),
            customdata=tel["Speed"],
            hovertemplate="%{customdata:.0f} km/h<extra></extra>",
            showlegend=False,
        ))

        try:
            circuit_info = session.get_circuit_info()
            corners = circuit_info.corners
            fig.add_trace(go.Scatter(
                x=corners["X"], y=corners["Y"], mode="markers+text",
                marker=dict(size=16, color="rgba(0,0,0,0)", line=dict(color=theme.GREY, width=1.4)),
                text=[str(n) for n in corners["Number"]],
                textfont=dict(size=10, color=theme.GREY),
                hoverinfo="skip", showlegend=False,
            ))
        except Exception:
            pass

        fig.update_yaxes(scaleanchor="x", scaleratio=1, visible=False)
        fig.update_xaxes(visible=False)
        theme.style_fig(fig, title=t("map.lap_title", driver=driver), height=620)
        fig.update_layout(plot_bgcolor=theme.BG_CARD, paper_bgcolor=theme.BG_CARD)
        st.plotly_chart(fig, width="stretch")

    top_speed = tel["Speed"].max()
    avg_speed = tel["Speed"].mean()
    m1, m2, m3 = st.columns(3)
    m1.metric(t("map.top_speed"), f"{top_speed:.0f} km/h")
    m2.metric(t("map.avg_speed"), f"{avg_speed:.0f} km/h")
    lap = session.laps.pick_drivers(driver).pick_fastest()
    laptime = str(lap["LapTime"])[10:] if lap is not None and not lap.empty else "-"
    m3.metric(t("map.lap_time"), laptime)

    prompt = (
        f"Pilote {driver}, tour le plus rapide de la session: {laptime}. "
        f"Vitesse max sur ce tour: {top_speed:.0f} km/h. Vitesse moyenne: {avg_speed:.0f} km/h. "
        "Commente brièvement ce qui ressort de ce tour (vitesse en ligne droite vs vitesse moyenne)."
    )
    ai_commentary.render_commentary(
        ai_commentary.session_key(session) + ("track_map", driver), prompt, get_lang()
    )
