
import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

import plotly.graph_objects as go
import streamlit as st

from app import ai_commentary, theme
from app.i18n import t, get_lang
from data import loader, processing as proc


def render_quali_vs_race(year: int, gp: str, race_session):
    st.markdown(theme.section_title(t("quali.title")), unsafe_allow_html=True)

    if race_session.name != "Race":
        st.info(t("quali.wrong_session"))
        return

    try:
        quali_session = loader.get_session(year, gp, "Q")
    except Exception as exc:
        st.warning(t("quali.unavailable", exc=exc))
        return

    merged = proc.get_quali_vs_race(quali_session, race_session)
    if merged.empty:
        st.info(t("quali.not_enough_data"))
        return

    top_gainer = merged.loc[merged["PositionsGained"].idxmax()]
    top_loser = merged.loc[merged["PositionsGained"].idxmin()]
    prompt = (
        f"Plus forte progression: {top_gainer['Abbreviation']} ({top_gainer['PositionsGained']:+.0f} places, "
        f"qualifs P{top_gainer['QualiPosition']:.0f} -> course P{top_gainer['RacePosition']:.0f}). "
        f"Plus forte perte: {top_loser['Abbreviation']} ({top_loser['PositionsGained']:+.0f} places, "
        f"qualifs P{top_loser['QualiPosition']:.0f} -> course P{top_loser['RacePosition']:.0f}). "
        "Commente brièvement ces deux performances contrastées."
    )
    ai_commentary.render_commentary(
        ai_commentary.session_key(race_session) + ("quali_vs_race",), prompt, get_lang()
    )

    driver_order = list(merged.sort_values("RacePosition")["Abbreviation"])
    colors = [
        theme.GREEN if g > 0 else (theme.RED if g < 0 else theme.GREY_DIM)
        for g in merged.sort_values("RacePosition")["PositionsGained"]
    ]

    col1, col2 = st.columns([3, 2])

    with col1:
        with st.container(border=True):
            m = merged.sort_values("RacePosition")
            fig = go.Figure(go.Bar(
                x=m["Abbreviation"], y=m["PositionsGained"],
                marker_color=colors,
                hovertemplate=t("quali.hover_grid_to_finish", q="%{customdata[0]}", r="%{customdata[1]}")
                              + "<br>%{y:+d} " + t("quali.places_axis").lower() + "<extra>%{x}</extra>",
                customdata=m[["QualiPosition", "RacePosition"]].values,
            ))
            fig.add_hline(y=0, line_color=theme.GREY_DIM)
            theme.style_fig(fig, title=t("quali.gained_lost_title"), height=400)
            fig.update_yaxes(title=t("quali.places_axis"))
            st.plotly_chart(fig, width="stretch")

    with col2:
        with st.container(border=True):
            m2 = merged.dropna(subset=["MedianRaceLapTime"]).sort_values("MedianRaceLapTime")
            fig2 = go.Figure(go.Bar(
                x=m2["MedianRaceLapTime"], y=m2["Abbreviation"], orientation="h",
                marker_color=theme.RED,
                hovertemplate="%{x:.3f}s<extra>%{y}</extra>",
            ))
            theme.style_fig(fig2, title=t("quali.pace_title"), height=400)
            fig2.update_xaxes(title=t("quali.time_axis"))
            fig2.update_yaxes(categoryorder="total descending", autorange="reversed")
            st.plotly_chart(fig2, width="stretch")

    with st.container(border=True):
        display = merged.sort_values("RacePosition").rename(columns={
            "Abbreviation": t("quali.col_driver"), "QualiPosition": t("quali.col_quali_grid"),
            "GridPosition": t("quali.col_start_grid"), "RacePosition": t("quali.col_finish"),
            "PositionsGained": t("quali.col_gain"), "MedianRaceLapTime": t("quali.col_pace"),
        })
        st.dataframe(display, width="stretch", hide_index=True)
