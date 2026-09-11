"""
Optional AI-generated data commentary: one short, factual block per tab,
written by Gemini from the numbers already computed for that tab (never
raw telemetry) so cost and hallucination risk both stay low.

Uses Google's Gemini API specifically because it has a real, permanent free
tier (ai.google.dev - no billing account needed) - unlike every other data
source in this dashboard, a commentary feature fundamentally needs an LLM
call, and this is the option that keeps the whole project keyless-or-free.
It's still fully optional: with no key configured, `render_commentary` is a
silent no-op everywhere it's called, and the rest of the dashboard works
exactly as before.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ROOT = _Path(__file__).resolve().parent.parent
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))

import os

import streamlit as st

MODEL = "gemini-3.8-flash"
CACHE_TTL_SECONDS = 1200  # 20 min - deliberately looser than the live data
# refresh interval (15-60s): re-writing the same commentary every refresh
# tick would be both expensive and distracting to read while it flickers.

SYSTEM_PROMPTS = {
    "fr": (
        "Tu es un analyste F1 concis qui commente un dashboard de données. "
        "Réponds en français, en 2 à 4 phrases de prose (pas de titre, pas de liste). "
        "Base-toi strictement sur les données fournies dans le message ; n'invente "
        "aucun fait, aucune donnée, aucun nom qui n'y figure pas."
    ),
    "en": (
        "You are a concise F1 analyst commenting on a data dashboard. "
        "Answer in English, in 2 to 4 sentences of plain prose (no heading, no list). "
        "Base your answer strictly on the data given in the message; never invent "
        "a fact, figure, or name that isn't in it."
    ),
}


def _get_client():
    try:
        from google import genai
    except ImportError:
        return None
    key = None
    try:
        key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    key = key or os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    return genai.Client(api_key=key)


def is_available() -> bool:
    return _get_client() is not None


def session_key(session) -> tuple:
    """Stable (year, event, session-type) tuple to seed a commentary cache
    key - combine with tab name and any driver/lap picks at the call site."""
    try:
        year = session.event["EventDate"].year
    except Exception:
        year = None
    return (year, session.event.get("EventName", "?"), session.name)


@st.cache_data(show_spinner=False, ttl=CACHE_TTL_SECONDS)
def _generate_cached(cache_key: tuple, prompt: str, lang: str) -> str | None:
    client = _get_client()
    if client is None:
        return None
    from google.genai import types

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS["fr"]),
                max_output_tokens=300,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
    except Exception:
        return None
    text = (response.text or "").strip()
    return text or None


_SPARKLE_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
    'stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M12 3v3M12 18v3M4.5 12h3M16.5 12h3'
    'M6.5 6.5l2 2M15.5 15.5l2 2M6.5 17.5l2-2M15.5 8.5l2-2"/>'
    "</svg>"
)


def render_commentary(cache_key: tuple, prompt: str, lang: str = "fr"):
    """Render a small AI-commentary card if a key is configured; a silent
    no-op otherwise (missing key, SDK missing, or a transient API error)."""
    if not is_available():
        return
    text = _generate_cached(cache_key, prompt, lang)
    if not text:
        return
    label = "Analyse IA" if lang == "fr" else "AI insight"
    st.markdown(
        f"""
        <div class="ai-commentary">
            <div class="ai-commentary-label">{_SPARKLE_SVG}{label}</div>
            <div class="ai-commentary-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
