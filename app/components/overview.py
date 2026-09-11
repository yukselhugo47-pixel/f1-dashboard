import streamlit as st

from app import ai_commentary, media, theme
from app.i18n import t, get_lang
from data import processing as proc

MEDAL_COLORS = {1: "#FFD700", 2: "#C7CBCF", 3: "#CD7F32"}


def render_overview(session):
    st.markdown(theme.section_title(t("overview.title")), unsafe_allow_html=True)
    summary = proc.get_race_summary(session)
    provisional = summary.get("is_provisional", False)

    lang = get_lang()
    podium_str = ", ".join(f"P{e['position']} {e['name']} ({e['team']})" for e in summary.get("podium", []))
    fastest = summary.get("fastest_lap", {})
    pole = summary.get("pole", {})
    sc_count = len(summary.get("safety_car_periods", []))
    prompt = (
        f"Podium: {podium_str or 'inconnu'}. "
        f"Pole: {pole.get('driver', 'inconnue')}. "
        f"Meilleur tour: {fastest.get('driver', '?')} en {fastest.get('time', '?')} au tour {fastest.get('lap', '?')}. "
        f"Interruptions safety car/VSC: {sc_count}. "
        f"Session {'provisoire, en cours' if provisional else 'terminée'}. "
        "Donne le fait le plus marquant de cette session."
    )
    ai_commentary.render_commentary(ai_commentary.session_key(session) + ("overview",), prompt, lang)

    if provisional:
        st.markdown(
            f'<span class="badge badge-sc"><span class="live-dot" style="margin-right:6px;"></span>'
            f'{t("overview.provisional_badge")}</span>',
            unsafe_allow_html=True,
        )
        st.write("")

    podium = summary.get("podium", [])
    if not podium:
        st.info(t("overview.no_podium"))
    cols = st.columns(3)
    for col, entry in zip(cols, podium):
        rank = entry["position"] or 0
        color = MEDAL_COLORS.get(rank, "#888")
        info = media.driver_info(session, entry["driver"])
        photo_html = (
            f'<img class="podium-photo" src="{info["headshot"]}" onerror="this.style.display=\'none\'" alt="">'
            if info["headshot"] else ""
        )
        logo_url = media.team_logo_url(info["team_id"])
        logo_html = (
            f'<img class="team-logo-inline" src="{logo_url}" onerror="this.style.display=\'none\'" alt="">'
            if logo_url else ""
        )
        with col:
            st.markdown(
                f"""
                <div class="podium-card" style="--accent:{color};">
                    <div class="podium-rank" style="color:{color};">P{rank}</div>
                    {photo_html}
                    <div class="podium-driver">{entry['name']}</div>
                    <div class="podium-team">{logo_html}{entry['team']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    stat_cols = st.columns(4)
    pole = summary.get("pole", {})
    fastest = summary.get("fastest_lap", {})
    weather = summary.get("weather", {})

    with stat_cols[0]:
        st.markdown(
            f'<div class="stat-block"><div class="stat-value">{pole.get("driver", "-")}</div>'
            f'<div class="stat-label">{t("overview.pole")}</div></div>',
            unsafe_allow_html=True,
        )
    with stat_cols[1]:
        st.markdown(
            f'<div class="stat-block"><div class="stat-value">{fastest.get("time", "-")}</div>'
            f'<div class="stat-label">{t("overview.fastest_lap", driver=fastest.get("driver", "-"), lap=fastest.get("lap", "-"))}</div></div>',
            unsafe_allow_html=True,
        )
    with stat_cols[2]:
        sc_count = len(summary.get("safety_car_periods", []))
        with stat_cols[2]:
            st.markdown(
                f'<div class="stat-block"><div class="stat-value">{sc_count}</div>'
                f'<div class="stat-label">{t("overview.sc_count")}</div></div>',
                unsafe_allow_html=True,
            )
    with stat_cols[3]:
        temp = weather.get("track_temp", "-")
        st.markdown(
            f'<div class="stat-block"><div class="stat-value">{temp}°C</div>'
            f'<div class="stat-label">{t("overview.track_temp")}</div></div>',
            unsafe_allow_html=True,
        )

    periods = summary.get("safety_car_periods", [])
    if periods:
        st.write("")
        badges = ""
        for p in periods:
            cls = "badge-sc" if "Virtual" not in p["type"] else "badge-vsc"
            try:
                start = p["start"].total_seconds() if hasattr(p["start"], "total_seconds") else p["start"]
                end = p["end"].total_seconds() if hasattr(p["end"], "total_seconds") else p["end"]
                span = f"{start/60:.0f}' – {end/60:.0f}'"
            except Exception:
                span = ""
            badges += f'<span class="badge {cls}">{p["type"]} {span}</span>'
        st.markdown(badges, unsafe_allow_html=True)

    with st.container(border=True):
        table_title = t("overview.table_provisional") if provisional else t("overview.table_final")
        st.markdown(theme.section_title(table_title, top_margin="0"), unsafe_allow_html=True)
        st.dataframe(proc.get_results_table(session, lang=get_lang()), width="stretch", hide_index=True, height=420)
