import plotly.graph_objects as go
import streamlit as st

from app import ai_commentary, theme
from app.i18n import t, get_lang
from data import processing as proc


def render_degradation_heatmap(session):
    st.markdown(theme.section_title(t("heat.title")), unsafe_allow_html=True)
    st.caption(t("heat.caption"))

    data = proc.get_degradation_heatmap(session)
    if data.empty:
        st.warning(t("heat.no_data"))
        return

    driver_order = proc.get_driver_abbreviations(session)
    driver_order = [d for d in driver_order if d in data["Driver"].unique()]

    pivot = data.pivot_table(index="Driver", columns="LapNumber", values="DeltaToMedian")
    pivot = pivot.reindex(driver_order)

    with st.container(border=True):
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale=[[0, "#3671C6"], [0.5, "#141417"], [1, "#E10600"]],
            zmid=0,
            zmin=-2, zmax=2,
            colorbar=dict(title=dict(text="Δs", font=dict(color=theme.TEXT)), tickfont=dict(color=theme.TEXT)),
            hovertemplate=t("cmp.lap") + " %{x}<br>%{y}<br>Δ %{z:.2f}s<extra></extra>",
            xgap=1, ygap=2,
        ))
        theme.style_fig(fig, title=t("heat.chart_title"), height=max(420, 22 * len(driver_order)))
        fig.update_xaxes(title=t("heat.lap_axis"))
        fig.update_yaxes(title="")
        st.plotly_chart(fig, width="stretch")

    by_driver = data.groupby("Driver")["DeltaToMedian"].max().sort_values()
    prompt = (
        f"Écart maximal au temps médian par pilote (plus haut = pneus plus dégradés à un moment de la "
        f"course), du plus régulier au plus dégradé: {by_driver.round(2).to_dict()}. "
        "Indique quel pilote a le mieux géré ses pneus et lequel a le plus souffert."
    )
    ai_commentary.render_commentary(
        ai_commentary.session_key(session) + ("degradation_heatmap",), prompt, get_lang()
    )
