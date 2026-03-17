"""Shared utility helpers used across modules."""

import os


def safe_int_env(name: str, default: int) -> int:
    """Parse int environment variables with a safe fallback."""
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def safe_float_env(name: str, default: float) -> float:
    """Parse float environment variables with a safe fallback."""
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def looks_like_timeout(exc: Exception) -> bool:
    """Best-effort check for timeout-like transport/runtime errors."""
    text = str(exc).lower()
    return (
        "timed out" in text
        or "timeout" in text
        or "connection error" in text
        or "connection reset" in text
        or "name resolution" in text
        or "proxyerror" in text
        or "forbidden" in text
    )
