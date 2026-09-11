
import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app import ai_commentary, media, theme
from app.i18n import t, get_lang
from data import processing as proc


def render_tire_strategy(session):
    st.markdown(theme.section_title(t("tire.title")), unsafe_allow_html=True)

    stints = proc.get_tire_stints(session)
    if stints.empty:
        st.warning(t("tire.no_stints"))
        return

    driver_order = proc.get_driver_abbreviations(session)
    driver_order = [d for d in driver_order if d in stints["Driver"].unique()]

    with st.container(border=True):
        fig = go.Figure()
        seen_compounds = set()
        for _, row in stints.iterrows():
            compound = row["Compound"]
            color = theme.compound_color(session, compound)
            show_legend = compound not in seen_compounds
            seen_compounds.add(compound)
            fig.add_trace(go.Bar(
                x=[row["Laps"]], y=[row["Driver"]], base=[row["StartLap"] - 1],
                orientation="h", marker=dict(color=color, line=dict(color=theme.BG_CARD, width=1)),
                name=compound, legendgroup=compound, showlegend=show_legend,
                hovertemplate=f"{compound}<br>{t('cmp.lap')} {int(row['StartLap'])}-{int(row['EndLap'])}"
                              f" ({int(row['Laps'])})<extra>{row['Driver']}</extra>",
            ))
        theme.style_fig(fig, title=t("tire.gantt_title"), height=max(420, 24 * len(driver_order)))
        fig.update_layout(barmode="stack", legend=dict(orientation="h", y=1.06))
        fig.update_yaxes(categoryorder="array", categoryarray=list(reversed(driver_order)), title="")
        fig.update_xaxes(title=t("cmp.lap"))
        st.plotly_chart(fig, width="stretch")

    stops_per_driver = stints.groupby("Driver").size() - 1
    compound_counts = stints["Compound"].value_counts().to_dict()
    prompt = (
        f"Nombre d'arrêts au stand par pilote (résumé): {stops_per_driver.value_counts().to_dict()} "
        f"(clé = nombre d'arrêts, valeur = nombre de pilotes). "
        f"Répartition des composés utilisés sur l'ensemble de la course: {compound_counts}. "
        "Décris la stratégie pneus dominante de cette course en une phrase ou deux."
    )
    ai_commentary.render_commentary(
        ai_commentary.session_key(session) + ("tire_gantt",), prompt, get_lang()
    )

    st.write("")
    st.markdown(theme.section_title(t("tire.degradation_title")), unsafe_allow_html=True)

    degradation = proc.get_stint_degradation(session)
    if degradation.empty:
        st.info(t("tire.no_clean_laps"))
        return

    focus = st.session_state.get("focus_driver")
    default_idx = driver_order.index(focus) if focus in driver_order else 0

    c1, c2 = st.columns([1, 2])
    driver = c1.selectbox(t("tire.driver"), driver_order, index=default_idx, key="deg_driver")
    st.session_state["focus_driver"] = driver
    c1.markdown(media.driver_badge_html(session, driver), unsafe_allow_html=True)
    car_html = media.team_car_html(session, driver)
    if car_html:
        c1.markdown(car_html, unsafe_allow_html=True)

    with c2:
        with st.container(border=True):
            drv_deg = degradation[degradation["Driver"] == driver].sort_values("Stint")
            if drv_deg.empty:
                st.info(t("tire.no_stint"))
            else:
                fig2 = go.Figure()
                for _, row in drv_deg.iterrows():
                    fig2.add_trace(go.Bar(
                        x=[t("tire.stint_label", n=int(row["Stint"]), compound=row["Compound"])],
                        y=[row["DegradationSlope"]],
                        marker_color=theme.compound_color(session, row["Compound"]),
                        hovertemplate="%{y:+.3f} " + t("tire.slope_axis") + "<extra></extra>",
                        showlegend=False,
                    ))
                theme.style_fig(fig2, title=t("tire.slope_title", driver=driver), height=340)
                fig2.add_hline(y=0, line_color=theme.GREY_DIM, line_dash="dot")
                fig2.update_yaxes(title=t("tire.slope_axis"))
                st.plotly_chart(fig2, width="stretch")

    laps = proc.get_lap_times_df(session, [driver])
    if "IsAccurate" in laps.columns:
        laps = laps[laps["IsAccurate"]]
    if not laps.empty:
        with st.container(border=True):
            fig3 = go.Figure()
            for stint, grp in laps.groupby("Stint"):
                grp = grp.dropna(subset=["TyreLife", "LapTimeSeconds"]).sort_values("TyreLife")
                if grp.empty:
                    continue
                compound = grp["Compound"].iloc[0]
                color = theme.compound_color(session, compound)
                fig3.add_trace(go.Scatter(
                    x=grp["TyreLife"], y=grp["LapTimeSeconds"], mode="markers",
                    marker=dict(color=color, size=7),
                    name=t("tire.stint_label", n=int(stint), compound=compound),
                    hovertemplate=t("tire.tyre_age", age="%{x}") + "<br>%{y:.3f}s<extra></extra>",
                ))
                if len(grp) >= 3:
                    x = grp["TyreLife"].to_numpy(dtype=float)
                    y = grp["LapTimeSeconds"].to_numpy(dtype=float)
                    slope, intercept = np.polyfit(x, y, 1)
                    xs = np.linspace(x.min(), x.max(), 20)
                    fig3.add_trace(go.Scatter(
                        x=xs, y=slope * xs + intercept, mode="lines",
                        line=dict(color=color, width=2, dash="dash"),
                        showlegend=False, hoverinfo="skip",
                    ))
            theme.style_fig(fig3, title=t("tire.laptime_vs_age_title", driver=driver), height=380)
            fig3.update_xaxes(title=t("tire.tyre_age_axis"))
            fig3.update_yaxes(title=t("tire.laptime_axis"))
            st.plotly_chart(fig3, width="stretch")
