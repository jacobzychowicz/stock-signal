from __future__ import annotations

from typing import Sequence

from .config import MIN_KEYWORD_LEN


def _normalize_term(term: str) -> str:
    term = term.strip()
    if not term:
        return ""
    if " " in term:
        return f'"{term}"'
    return term


def normalize_keywords(raw_keywords: Sequence[str] | None) -> tuple[list[str], list[str]]:
    """
    Split comma-separated keywords, trim, drop empties, and collect too-short ones.
    Returns (usable_keywords, skipped_keywords).
    """
    if not raw_keywords:
        return [], []

    usable: list[str] = []
    skipped: list[str] = []

    for item in raw_keywords:
        parts = item.split(",")
        for part in parts:
            kw = part.strip()
            if not kw:
                continue
            if len(kw) < MIN_KEYWORD_LEN:
                skipped.append(kw)
                continue
            usable.append(kw)

    return usable, skipped


def normalize_for_query(keywords: Sequence[str] | None) -> list[str]:
    if not keywords:
        return []
    normalized = [_normalize_term(k) for k in keywords]
    return [k for k in normalized if k]
