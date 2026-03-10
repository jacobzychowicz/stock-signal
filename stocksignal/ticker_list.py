"""Load full ticker list from an external CSV. No hand-maintained list needed."""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING

from .config import POPULAR_TICKERS, TICKER_LIST_CSV_URL

if TYPE_CHECKING:
    from collections.abc import Sequence


def load_ticker_list_from_source(
    url: str = TICKER_LIST_CSV_URL,
    fallback: list[tuple[str, str]] | None = None,
) -> list[tuple[str, str]]:
    """
    Fetch CSV from url (expected: Symbol, Security Name or similar columns).
    Returns list of (symbol, display_name). Uses fallback list on failure.
    """
    fallback = fallback or POPULAR_TICKERS
    try:
        import requests  # type: ignore
    except ModuleNotFoundError:
        return fallback
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        text = resp.text
    except Exception:
        return fallback

    rows: list[tuple[str, str]] = []
    try:
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            # Support "Symbol" / "Security Name" (NASDAQ dataset) or similar
            sym = (row.get("Symbol") or row.get("symbol") or "").strip()
            name = (
                row.get("Security Name")
                or row.get("Name")
                or row.get("name")
                or row.get("Company")
                or sym
            )
            if isinstance(name, str):
                name = name.strip()
            else:
                name = str(name).strip()
            if sym:
                rows.append((sym, name or sym))
    except Exception:
        return fallback
    return rows if rows else fallback


def filter_tickers(
    tickers: Sequence[tuple[str, str]],
    query: str,
    limit: int = 50,
) -> list[tuple[str, str]]:
    """Case-insensitive substring match on symbol and name; return first `limit`."""
    q = (query or "").strip().lower()
    if not q or len(q) < 2:
        return []
    out: list[tuple[str, str]] = []
    for sym, name in tickers:
        if q in sym.lower() or q in name.lower():
            out.append((sym, name))
            if len(out) >= limit:
                break
    return out
