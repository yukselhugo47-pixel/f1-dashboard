
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


def render_driver_comparison(session):
    st.markdown(theme.section_title(t("cmp.title")), unsafe_allow_html=True)

    drivers = proc.get_driver_abbreviations(session)
    if len(drivers) < 2:
        st.warning(t("cmp.no_drivers"))
        return

    focus = st.session_state.get("focus_driver")
    default_idx = drivers.index(focus) if focus in drivers else 0

    c1, c2 = st.columns(2)
    drv1 = c1.selectbox(t("cmp.driver_a"), drivers, index=default_idx, key="cmp_drv1")
    st.session_state["focus_driver"] = drv1
    remaining = [d for d in drivers if d != drv1]
    drv2 = c2.selectbox(t("cmp.driver_b"), remaining, index=0, key="cmp_drv2")

    b1, b2 = st.columns(2)
    b1.markdown(media.driver_badge_html(session, drv1), unsafe_allow_html=True)
    b2.markdown(media.driver_badge_html(session, drv2), unsafe_allow_html=True)

    laps = proc.get_lap_times_df(session, [drv1, drv2])
    if laps.empty:
        st.info(t("cmp.no_laps"))
        return

    color1 = theme.driver_color(session, drv1, 0)
    color2 = theme.driver_color(session, drv2, 1)

    best1 = laps[laps["Driver"] == drv1]["LapTimeSeconds"].min()
    best2 = laps[laps["Driver"] == drv2]["LapTimeSeconds"].min()
    prompt = (
        f"Meilleur tour {drv1}: {best1:.3f}s. Meilleur tour {drv2}: {best2:.3f}s. "
        f"Écart: {abs(best1 - best2):.3f}s en faveur de {drv1 if best1 < best2 else drv2}. "
        "Compare brièvement le rythme de ces deux pilotes."
    )
    ai_commentary.render_commentary(
        ai_commentary.session_key(session) + ("comparison", drv1, drv2), prompt, get_lang()
    )

    with st.container(border=True):
        fig = go.Figure()
        for drv, color in [(drv1, color1), (drv2, color2)]:
            d = laps[laps["Driver"] == drv].sort_values("LapNumber")
            fig.add_trace(go.Scatter(
                x=d["LapNumber"], y=d["LapTimeSeconds"], mode="lines+markers",
                name=drv, line=dict(color=color, width=2.5), marker=dict(size=5),
                hovertemplate=t("cmp.lap") + " %{x}<br>%{y:.3f}s<extra>" + drv + "</extra>",
            ))
        theme.style_fig(fig, title=t("cmp.laptimes_title"), height=380)
        fig.update_yaxes(title=t("cmp.time_s"))
        fig.update_xaxes(title=t("cmp.lap"))
        st.plotly_chart(fig, width="stretch")

    col_delta, col_sector = st.columns([3, 2])

    with col_delta:
        with st.container(border=True):
            delta_df = proc.get_cumulative_delta(session, drv1, drv2)
            if delta_df.empty:
                st.info(t("cmp.no_delta"))
            else:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=delta_df["Distance"], y=delta_df["Delta"], mode="lines",
                    line=dict(color=color2, width=2.5), fill="tozeroy",
                    fillcolor=color2 + "22",
                    hovertemplate="%{x:.0f}m<br>%{y:+.3f}s<extra></extra>",
                ))
                fig2.add_hline(y=0, line_color=theme.GREY_DIM, line_dash="dot")
                theme.style_fig(fig2, title=t("cmp.delta_title", b=drv2, a=drv1), height=340)
                fig2.update_yaxes(title=t("cmp.delta_s"))
                fig2.update_xaxes(title=t("cmp.distance_m"))
                st.plotly_chart(fig2, width="stretch")

    with col_sector:
        with st.container(border=True):
            sectors = proc.get_sector_comparison(session, [drv1, drv2])
            if sectors.empty:
                st.info(t("cmp.no_sectors"))
            else:
                fig3 = go.Figure()
                colors = {drv1: color1, drv2: color2}
                for _, row in sectors.iterrows():
                    fig3.add_trace(go.Bar(
                        x=["S1", "S2", "S3"],
                        y=[row["Sector 1"], row["Sector 2"], row["Sector 3"]],
                        name=row["Driver"], marker_color=colors.get(row["Driver"]),
                        hovertemplate="%{x}: %{y:.3f}s<extra>" + row["Driver"] + "</extra>",
                    ))
                theme.style_fig(fig3, title=t("cmp.sectors_title"), height=340)
                fig3.update_layout(barmode="group")
                fig3.update_yaxes(title=t("cmp.time_s"))
                st.plotly_chart(fig3, width="stretch")
