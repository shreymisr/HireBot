"""
HireBot — AI-Powered Hiring Assistant
"""

import json
import os
from datetime import datetime, timezone

import streamlit as st
from dotenv import load_dotenv

from config import (
    APP_SUBTITLE,
    APP_TITLE,
    EXIT_KEYWORDS,
    EXIT_MESSAGE,
    GREETING_MESSAGE,
    GROQ_MODEL,
    PROFILE_FIELD_LABELS,
    PROFILE_FIELDS,
    STAGE_LABELS,
    STAGES,
)
from llm import get_response, is_api_key_set
from sentiment import analyze as analyze_sentiment

load_dotenv()

st.set_page_config(
    page_title=f"{APP_TITLE} — {APP_SUBTITLE}",
    page_icon=":robot_face:",
    layout="centered",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    :root {
        --navy:        #0f1b2d;
        --navy-light:  #1a2942;
        --navy-mid:    #243551;
        --accent:      #4a90d9;
        --accent-glow: rgba(74, 144, 217, 0.35);
        --white:       #ffffff;
        --off-white:   #f0f2f6;
        --text-muted:  #8899aa;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--navy) 0%, var(--navy-light) 100%) !important;
    }
    section[data-testid="stSidebar"] * { color: var(--off-white) !important; }
    section[data-testid="stSidebar"] .stTextInput label,
    section[data-testid="stSidebar"] .stCaption { color: var(--text-muted) !important; }
    section[data-testid="stSidebar"] hr { border-color: var(--navy-mid) !important; }

    .hb-header { text-align: center; padding: 1.8rem 0 0.4rem; }
    .hb-header .hb-title {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--accent), #6fc3df);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .hb-header p { color: var(--text-muted); font-size: 0.95rem; margin-top: 0.25rem; }

    .hb-stages {
        display: flex; justify-content: center; gap: 0.45rem;
        padding: 0.6rem 0; margin-bottom: 0.5rem; flex-wrap: wrap;
    }
    .hb-pill {
        padding: 0.3rem 0.75rem; border-radius: 999px;
        font-size: 0.75rem; font-weight: 500;
        transition: all 0.3s ease; white-space: nowrap;
    }
    .hb-pill.active {
        background: linear-gradient(135deg, var(--accent), #6fc3df);
        color: var(--white);
        box-shadow: 0 2px 10px var(--accent-glow);
    }
    .hb-pill.done    { background: #d1fae5; color: #065f46; }
    .hb-pill.pending { background: var(--off-white); color: #9ca3af; }

    .hb-divider {
        border: none; height: 1px;
        background: linear-gradient(90deg, transparent, #e5e7eb, transparent);
        margin: 0 0 1rem;
    }

    .stChatMessage { border-radius: 14px !important; }

    .profile-card {
        background: var(--navy-mid);
        border: 1px solid rgba(74, 144, 217, 0.25);
        border-radius: 12px; padding: 1rem; margin-top: 0.5rem;
    }
    .profile-card .pc-row {
        display: flex; justify-content: space-between;
        padding: 0.35rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        font-size: 0.82rem;
    }
    .profile-card .pc-row:last-child { border-bottom: none; }
    .profile-card .pc-label { color: var(--text-muted) !important; font-weight: 500; }
    .profile-card .pc-value { color: var(--off-white) !important; text-align: right; max-width: 60%; word-break: break-word; }
    .profile-card .pc-empty { color: rgba(255,255,255,0.2) !important; font-style: italic; }

    .gdpr-banner {
        background: var(--navy-mid);
        border-left: 3px solid var(--accent);
        border-radius: 6px; padding: 0.6rem 0.8rem; margin-top: 0.6rem;
        font-size: 0.72rem; line-height: 1.45;
        color: var(--text-muted) !important;
    }

    .sentiment-badge {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

_SENTIMENT_BADGE = {
    "POSITIVE": '<span class="sentiment-badge" style="background:#16a34a;color:#fff;">Positive</span>',
    "NEUTRAL":  '<span class="sentiment-badge" style="background:#6b7280;color:#fff;">Neutral</span>',
    "NEGATIVE": '<span class="sentiment-badge" style="background:#dc2626;color:#fff;">Negative</span>',
}


def _init_state():
    defaults = {
        "messages":          [],
        "stage":             "greeting",
        "initialized":       False,
        "candidate_profile": {},
        "profile_field_index": 0,
        "sentiment_history": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _render_sidebar():
    with st.sidebar:
        st.header("Configuration")

        if os.environ.get("GROQ_API_KEY"):
            st.success("API key loaded from environment")
        else:
            api_key = st.text_input(
                "Groq API Key",
                type="password",
                placeholder="gsk_...",
                help="Get your free key at https://console.groq.com",
            )
            if api_key:
                st.session_state.groq_api_key = api_key
                st.success("API key set for this session")
            else:
                st.warning("Enter your Groq API key to begin")

        st.divider()
        st.caption(f"**Model:** `{GROQ_MODEL}`")
        st.caption("**Powered by** Groq")

        st.divider()
        st.subheader("Candidate Profile")

        profile = st.session_state.get("candidate_profile", {})
        rows_html = ""
        for field in PROFILE_FIELDS:
            label = PROFILE_FIELD_LABELS.get(field, field)
            if field in profile:
                rows_html += (
                    f'<div class="pc-row">'
                    f'<span class="pc-label">{label}</span>'
                    f'<span class="pc-value">{profile[field]}</span>'
                    f"</div>"
                )
            else:
                rows_html += (
                    f'<div class="pc-row">'
                    f'<span class="pc-label">{label}</span>'
                    f'<span class="pc-value pc-empty">pending...</span>'
                    f"</div>"
                )
        st.markdown(f'<div class="profile-card">{rows_html}</div>', unsafe_allow_html=True)

        if profile:
            export_data = {
                "exported_at":       datetime.now(timezone.utc).isoformat(),
                "candidate_profile": profile,
                "conversation":      st.session_state.messages,
                "sentiment_history": st.session_state.get("sentiment_history", []),
                "stage":             st.session_state.stage,
            }
            st.download_button(
                label="Export Session (JSON)",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"hirebot_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )
            st.markdown(
                '<div class="gdpr-banner">'
                "<b>Data Notice:</b> This export contains personal data "
                "collected during the interview. Handle in accordance with "
                "GDPR / applicable data-protection regulations. Do not share "
                "without the candidate's explicit consent."
                "</div>",
                unsafe_allow_html=True,
            )

        history = st.session_state.get("sentiment_history", [])
        if history:
            st.divider()
            st.subheader("Candidate Sentiment")

            latest = history[-1]
            badge = _SENTIMENT_BADGE.get(latest["label"], _SENTIMENT_BADGE["NEUTRAL"])
            st.markdown(f"**Latest:** {badge}", unsafe_allow_html=True)
            st.progress(latest["score"], text=f"{latest['score']:.0%}")

            if len(history) >= 2:
                st.caption("**Session Trend**")
                st.line_chart({"Positivity": [h["score"] for h in history]}, height=150)


def _render_header():
    st.markdown(
        f'<div class="hb-header">'
        f'<div class="hb-title">{APP_TITLE}</div>'
        f"<p>{APP_SUBTITLE}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_stage_tracker():
    current_idx = STAGES.index(st.session_state.stage)
    pills = []
    for i, stage in enumerate(STAGES):
        label = STAGE_LABELS[stage]
        if i < current_idx:
            cls = "done"
        elif i == current_idx:
            cls = "active"
        else:
            cls = "pending"
        pills.append(f'<span class="hb-pill {cls}">{label}</span>')

    st.markdown(
        f'<div class="hb-stages">{"".join(pills)}</div>'
        '<hr class="hb-divider">',
        unsafe_allow_html=True,
    )


def _render_chat_history():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])


def _add_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})


def _is_exit(text: str) -> bool:
    return text.strip().lower() in EXIT_KEYWORDS


def _process_input(user_input: str):
    _add_message("user", user_input)

    if not is_api_key_set():
        _add_message(
            "assistant",
            "I need a **Groq API key** to respond. "
            "Please enter your key in the sidebar under Configuration, "
            "then send your message again.",
        )
        return

    sentiment_result = analyze_sentiment(user_input)
    st.session_state.sentiment_history.append(sentiment_result)

    if _is_exit(user_input):
        st.session_state.stage = "closing"
        _add_message("assistant", EXIT_MESSAGE)
        return

    prev_stage = st.session_state.stage

    if prev_stage in ("gathering_info", "tech_stack"):
        idx = st.session_state.profile_field_index
        if idx < len(PROFILE_FIELDS):
            field = PROFILE_FIELDS[idx]
            st.session_state.candidate_profile[field] = user_input.strip()

    stage, response = get_response(
        st.session_state.messages,
        candidate_profile=st.session_state.candidate_profile,
        current_stage=prev_stage,
    )

    if stage:
        st.session_state.stage = stage

    if prev_stage in ("gathering_info", "tech_stack"):
        idx = st.session_state.profile_field_index
        if idx < len(PROFILE_FIELDS):
            st.session_state.profile_field_index = idx + 1

    _add_message("assistant", response)


def main():
    _init_state()
    _render_sidebar()
    _render_header()
    _render_stage_tracker()

    if not st.session_state.initialized:
        _add_message("assistant", GREETING_MESSAGE)
        st.session_state.initialized = True

    _render_chat_history()

    is_closed = st.session_state.stage == "closing"
    placeholder = (
        "Interview complete — refresh to start a new session"
        if is_closed
        else "Type your response here..."
    )

    if prompt := st.chat_input(placeholder, disabled=is_closed):
        _process_input(prompt)
        st.rerun()


if __name__ == "__main__":
    main()
