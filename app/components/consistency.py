import plotly.graph_objects as go
import streamlit as st

from app import ai_commentary, theme
from app.i18n import t, get_lang
from data import processing as proc


def render_consistency(session):
    st.markdown(theme.section_title(t("cons.title")), unsafe_allow_html=True)
    st.caption(t("cons.caption"))

    stats = proc.get_consistency_ranking(session)
    if stats.empty:
        st.warning(t("cons.no_data"))
        return

    most_consistent = stats.iloc[0]
    least_consistent = stats.iloc[-1]
    prompt = (
        f"Pilote le plus régulier: {most_consistent['Driver']} (écart-type {most_consistent['StdDev']:.3f}s). "
        f"Pilote le moins régulier: {least_consistent['Driver']} (écart-type {least_consistent['StdDev']:.3f}s). "
        "Commente brièvement cet écart de régularité."
    )
    ai_commentary.render_commentary(
        ai_commentary.session_key(session) + ("consistency",), prompt, get_lang()
    )

    with st.container(border=True):
        fig = go.Figure(go.Bar(
            x=stats["StdDev"], y=stats["Driver"], orientation="h",
            marker=dict(
                color=stats["StdDev"],
                colorscale=[[0, theme.GREEN], [0.5, "#F4B400"], [1, theme.RED]],
            ),
            customdata=stats[["MeanLapTime", "CleanLaps"]].values,
            hovertemplate=t("cons.col_stddev") + " %{x:.3f}s<br>" + t("cons.col_mean")
                          + " %{customdata[0]:.3f}s<br>%{customdata[1]:.0f}<extra>%{y}</extra>",
        ))
        theme.style_fig(fig, title=t("cons.stddev_title"), height=max(420, 24 * len(stats)))
        fig.update_yaxes(categoryorder="array", categoryarray=list(stats.sort_values("StdDev", ascending=False)["Driver"]), title="")
        fig.update_xaxes(title=t("cons.stddev_axis"))
        st.plotly_chart(fig, width="stretch")

    with st.container(border=True):
        display = stats.rename(columns={
            "Driver": t("cons.col_driver"), "StdDev": t("cons.col_stddev"),
            "MeanLapTime": t("cons.col_mean"), "CleanLaps": t("cons.col_clean_laps"),
        })
        st.dataframe(display, width="stretch", hide_index=True)
