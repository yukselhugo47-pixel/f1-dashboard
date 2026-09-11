"""Colors and plotly styling shared by every chart in the dashboard."""
from __future__ import annotations

import fastf1.plotting as fp

BG = "#0A0A0C"
BG_CARD = "#141417"
BG_CARD_ALT = "#1A1A1E"
RED = "#E10600"
RED_DIM = "#8C0400"
GREY = "#9BA1A6"
GREY_DIM = "#848A93"
TEXT = "#F2F2F2"
GRID = "#2A2A2E"
GREEN = "#22C55E"

FALLBACK_PALETTE = [
    RED, "#3671C6", "#27F4D2", "#FF8000", "#229971",
    "#FF87BC", "#64C4FF", "#6692FF", "#52E252", "#B6BABD",
]

HEADER_FONT = "'Oswald', 'Titillium Web', sans-serif"
BODY_FONT = "'Titillium Web', 'Segoe UI', sans-serif"


def driver_color(session, driver: str, idx: int = 0) -> str:
    try:
        return fp.get_driver_color(driver, session)
    except Exception:
        return FALLBACK_PALETTE[idx % len(FALLBACK_PALETTE)]


def team_color(session, team: str, idx: int = 0) -> str:
    try:
        return fp.get_team_color(team, session)
    except Exception:
        return FALLBACK_PALETTE[idx % len(FALLBACK_PALETTE)]


def compound_color(session, compound: str) -> str:
    try:
        return fp.get_compound_color(compound, session)
    except Exception:
        return "#CCCCCC"


PLOTLY_LAYOUT = dict(
    paper_bgcolor=BG_CARD,
    plot_bgcolor=BG_CARD,
    font=dict(color=TEXT, family=BODY_FONT, size=13),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)"),
    margin=dict(l=50, r=20, t=55, b=45),
    hoverlabel=dict(bgcolor="#1c1c20", font_size=13, font_family=BODY_FONT, bordercolor=RED),
    hovermode="closest",
    transition=dict(duration=350, easing="cubic-in-out"),
)


def section_title(text: str, top_margin: str | None = None) -> str:
    """Real <h2> (styled via the .section-title class) so screen readers can
    navigate the page by heading instead of the old look-alike <div>."""
    style = f' style="margin-top:{top_margin};"' if top_margin else ""
    return f'<h2 class="section-title"{style}>{text}</h2>'


def style_fig(fig, title: str | None = None, height: int | None = None):
    fig.update_layout(**PLOTLY_LAYOUT)
    if title:
        fig.update_layout(title=dict(text=title, font=dict(size=17, family=HEADER_FONT, color=TEXT), x=0.01, xanchor="left"))
    if height:
        fig.update_layout(height=height)
    fig.update_xaxes(gridcolor=GRID, zerolinecolor="#3a3a3e", linecolor=GRID, showspikes=False)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor="#3a3a3e", linecolor=GRID)
    return fig
