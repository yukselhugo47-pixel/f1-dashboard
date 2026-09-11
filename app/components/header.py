import pandas as pd
import streamlit as st

from app.i18n import t


def render_header(session, summary: dict, is_live: bool = False):
    event = session.event
    provisional = summary.get("is_provisional", False)
    podium = summary.get("podium", [])
    leader = podium[0]["name"] if podium else "-"
    leader_label = t("header.leading") if provisional else t("header.winner")
    try:
        date_str = event["EventDate"].strftime("%d %b %Y")
    except Exception:
        date_str = str(event.get("EventDate", "-"))

    live_badge = ""
    if is_live:
        now_str = pd.Timestamp.now().strftime("%H:%M:%S")
        live_badge = (
            f'<div class="info-chip"><span class="live-badge">'
            f'<span class="live-dot"></span>{t("sidebar.live_badge")}</span>'
            f'<span class="value" style="font-size:12px;color:var(--grey);">{t("header.updated", time=now_str)}</span></div>'
        )

    logo_svg = (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>'
        '<line x1="4" y1="22" x2="4" y2="15"/>'
        "</svg>"
    )
    st.markdown(
        f"""
        <div class="f1-header">
            <div class="f1-header-title">
                <span class="f1-logo">{logo_svg}</span>
                <div>
                    <h1 class="f1-title">PADDOCK<span class="accent">ANALYTICS</span></h1>
                    <div class="f1-subtitle">{event.get('EventName', '')} &middot; {session.name}</div>
                </div>
            </div>
            <div class="f1-header-info">
                {live_badge}
                <div class="info-chip"><span class="label">{t('header.circuit')}</span><span class="value">{event.get('Location', '-')}, {event.get('Country', '-')}</span></div>
                <div class="info-chip"><span class="label">{t('header.date')}</span><span class="value">{date_str}</span></div>
                <div class="info-chip"><span class="label">{leader_label}</span><span class="value">{leader}</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
