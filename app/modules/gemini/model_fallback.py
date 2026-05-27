"""Fallback entre modelos gratuitos quando a cota do Gemini esgota."""

import logging
from collections.abc import Iterator

from google.genai import errors as genai_errors

from app.config import GEMINI_DYNAMIC, GEMINI_MODEL

logger = logging.getLogger(__name__)

# Modelos gratuitos (ordem de tentativa após GEMINI_MODEL).
FREE_TIER_MODELS: tuple[str, ...] = (
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-robotics-er-1.6-preview",
)

_QUOTA_KEYWORDS = (
    "quota",
    "rate limit",
    "rate_limit",
    "resource_exhausted",
    "resource exhausted",
    "too many requests",
    "exceeded",
    "limit:",
)


def is_quota_error(exc: BaseException) -> bool:
    """Indica se o erro parece ser limite de cota / taxa do modelo."""
    if isinstance(exc, genai_errors.APIError):
        if exc.code in (429, 503):
            return True
        status = (exc.status or "").upper()
        if status in ("RESOURCE_EXHAUSTED", "UNAVAILABLE"):
            return True

    text = str(exc).lower()
    return any(keyword in text for keyword in _QUOTA_KEYWORDS)


def models_to_try() -> Iterator[str]:
    """
    Gera modelos na ordem de tentativa.

    Sempre começa por GEMINI_MODEL. Com GEMINI_DYNAMIC=true, segue a lista
    FREE_TIER_MODELS sem repetir o primário.
    """
    if not GEMINI_MODEL:
        raise ValueError("GEMINI_MODEL não está definido no ambiente.")

    yield GEMINI_MODEL

    if not GEMINI_DYNAMIC:
        return

    for model in FREE_TIER_MODELS:
        if model != GEMINI_MODEL:
            yield model
