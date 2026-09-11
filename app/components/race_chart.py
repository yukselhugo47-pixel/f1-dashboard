import plotly.graph_objects as go
import streamlit as st

from app import ai_commentary, theme
from app.i18n import t, get_lang
from data import processing as proc


def render_race_chart(session):
    st.markdown(theme.section_title(t("race.title")), unsafe_allow_html=True)

    pos_df = proc.get_position_by_lap(session)
    if pos_df.empty:
        st.warning(t("race.no_data"))
        return

    driver_order = proc.get_driver_abbreviations(session)
    default_selection = driver_order[:10] if len(driver_order) > 10 else driver_order
    selected = st.multiselect(t("race.drivers_shown"), driver_order, default=default_selection, key="race_chart_drivers")
    if not selected:
        st.info(t("race.select_one"))
        return

    with st.container(border=True):
        fig = go.Figure()
        for idx, drv in enumerate(selected):
            d = pos_df[pos_df["Driver"] == drv].sort_values("LapNumber")
            if d.empty:
                continue
            color = theme.driver_color(session, drv, idx)
            fig.add_trace(go.Scatter(
                x=d["LapNumber"], y=d["Position"], mode="lines+markers",
                name=drv, line=dict(color=color, width=2.3, shape="hv"), marker=dict(size=4),
                hovertemplate=t("cmp.lap") + " %{x}<br>P%{y}<extra>" + drv + "</extra>",
            ))
        theme.style_fig(fig, title=t("race.position_title"), height=560)
        fig.update_yaxes(title=t("race.position_axis"), autorange="reversed", dtick=1)
        fig.update_xaxes(title=t("cmp.lap"))
        fig.update_layout(legend=dict(orientation="v", y=1, x=1.02))
        st.plotly_chart(fig, width="stretch")

    changes = []
    for drv in selected:
        d = pos_df[pos_df["Driver"] == drv].sort_values("LapNumber")
        if len(d) >= 2:
            changes.append((drv, int(d["Position"].iloc[0]), int(d["Position"].iloc[-1])))
    prompt = (
        f"Positions (tour 1 -> dernier tour connu) pour les pilotes affichés: "
        f"{[(d, s, e) for d, s, e in changes]}. "
        "Identifie le pilote qui a le plus gagné et celui qui a le plus perdu de places."
    )
    ai_commentary.render_commentary(
        ai_commentary.session_key(session) + ("race_chart", tuple(sorted(selected))), prompt, get_lang()
    )
