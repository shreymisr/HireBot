"""
HireBot — LLM Integration (Groq)
"""

import os
import re

import streamlit as st
from groq import Groq

from config import GROQ_MODEL, STAGES, SYSTEM_PROMPT, TECH_STACK_INJECTION

_STAGE_RE = re.compile(r"\[STAGE:\s*(\w+)\s*\]")


def _get_api_key() -> str | None:
    return os.environ.get("GROQ_API_KEY") or st.session_state.get("groq_api_key")


def is_api_key_set() -> bool:
    return bool(_get_api_key())


def _get_client() -> Groq:
    api_key = _get_api_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured.")
    return Groq(api_key=api_key)


def _parse_stage_marker(text: str) -> tuple[str, str]:
    """
    Extract [STAGE:xxx] from the model response.

    Returns (stage_name, cleaned_text). stage_name is empty if the marker
    is absent or does not match a known stage — callers preserve the
    current stage in that case.
    """
    match = _STAGE_RE.search(text)
    if match and match.group(1) in STAGES:
        stage = match.group(1)
        cleaned = _STAGE_RE.sub("", text, count=1).strip()
        return stage, cleaned
    return "", text


def get_response(
    messages: list[dict],
    candidate_profile: dict | None = None,
    current_stage: str = "",
) -> tuple[str, str]:
    """
    Send chat history to Groq and return (detected_stage, response_text).

    Injects a secondary system message with per-technology questioning
    instructions once the tech stack field has been collected, ensuring
    the model generates structured questions for every technology listed.
    """
    client = _get_client()

    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    tech_stack = (candidate_profile or {}).get("tech_stack", "")
    if tech_stack and current_stage in ("tech_stack", "questioning"):
        api_messages.append({
            "role": "system",
            "content": TECH_STACK_INJECTION.format(tech_stack=tech_stack),
        })

    api_messages.extend(
        {"role": m["role"], "content": m["content"]} for m in messages
    )

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=api_messages,
            temperature=0.7,
            max_tokens=1024,
        )
        raw = completion.choices[0].message.content or ""
        return _parse_stage_marker(raw)

    except Exception as exc:
        return "", (
            "I'm experiencing a momentary issue — please try again.\n\n"
            f"_Error: {exc!s}_"
        )
