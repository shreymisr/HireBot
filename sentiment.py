"""
HireBot — Sentiment Analysis
DistilBERT-based sentiment pipeline with factual-input skip logic.

Short or factual inputs (names, emails, phone numbers, single-word answers)
are unreliable for sentiment — they are skipped and default to Neutral rather
than polluting the trend chart with spurious scores.
"""

import re
import logging

import streamlit as st
from transformers import pipeline

logging.getLogger("huggingface_hub.file_download").setLevel(logging.ERROR)

SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"

_MIN_CHARS = 25
_POSITIVE_THRESHOLD = 0.75
_NEGATIVE_THRESHOLD = 0.80

_FACTUAL_PATTERNS = re.compile(
    r"^("
    r"[\w.+-]+@[\w-]+\.[a-z]{2,}"          # email
    r"|\+?[\d\s\-().]{7,15}"               # phone
    r"|[A-Z][a-z]+ [A-Z][a-z]+"           # "First Last" name
    r"|\d{1,2}(\.\d)?\s*(years?|yrs?)?"   # years of experience
    r"|[a-zA-Z]{1,20}"                     # single word
    r")$",
    re.IGNORECASE,
)

_NEUTRAL_RESULT = {"label": "NEUTRAL", "score": 0.5}


@st.cache_resource(show_spinner="Loading sentiment model...")
def _load_pipeline():
    return pipeline("sentiment-analysis", model=SENTIMENT_MODEL, device=-1)


def _should_skip(text: str) -> bool:
    """
    Return True for inputs where sentiment is meaningless — short or purely
    factual answers that DistilBERT was not trained to interpret accurately.
    """
    stripped = text.strip()
    if len(stripped) < _MIN_CHARS:
        return True
    return bool(_FACTUAL_PATTERNS.match(stripped))


def analyze(text: str) -> dict:
    """
    Run sentiment analysis and return a result dict.

    Skips analysis for short/factual inputs (returns Neutral).
    Applies conservative thresholds to reduce false POSITIVE/NEGATIVE labels.

    Returns: {"label": "POSITIVE"|"NEUTRAL"|"NEGATIVE", "score": float}
    """
    if _should_skip(text):
        return _NEUTRAL_RESULT.copy()

    try:
        result = _load_pipeline()(text, truncation=True, max_length=512)[0]
        raw_label: str = result["label"]
        raw_score: float = result["score"]

        if raw_label == "POSITIVE" and raw_score > _POSITIVE_THRESHOLD:
            return {"label": "POSITIVE", "score": round(raw_score, 3)}
        if raw_label == "NEGATIVE" and raw_score > _NEGATIVE_THRESHOLD:
            return {"label": "NEGATIVE", "score": round(1.0 - raw_score, 3)}
        return {"label": "NEUTRAL", "score": 0.5}

    except Exception:
        return _NEUTRAL_RESULT.copy()
