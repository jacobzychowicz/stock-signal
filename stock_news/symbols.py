from __future__ import annotations

from .config import YAHOO_SEARCH_URL


def search_symbols(query: str, limit: int = 10) -> list[tuple[str, str]]:
    """
    Search Yahoo Finance for tickers/companies matching the query.
    Returns list of (symbol, display_name) for autocomplete/dropdowns.
    """
    q = (query or "").strip()
    if not q or len(q) < 2:
        return []

    try:
        import requests  # type: ignore
    except ModuleNotFoundError:
        return []

    try:
        resp = requests.get(
            YAHOO_SEARCH_URL,
            params={"q": q, "quotesCount": min(limit, 20), "newsCount": 0},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    results: list[tuple[str, str]] = []
    seen: set[str] = set()
    for quote in data.get("quotes", []):
        sym = (quote.get("symbol") or "").strip().upper()
        if not sym or sym in seen:
            continue
        seen.add(sym)
        name = (quote.get("longname") or quote.get("shortname") or sym) or sym
        results.append((sym, str(name).strip()))
    return results[:limit]


def looks_like_ticker(symbol: str) -> bool:
    """
    Heuristic: short, uppercase-ish, no spaces. Allows dots/slashes for tickers like BRK.B.
    """
    sym = symbol.strip()
    if not sym or " " in sym:
        return False
    if len(sym) > 6:
        return False
    alnumish = sym.replace(".", "").replace("-", "").replace("/", "")
    return alnumish.isalnum()


def expand_symbol_to_company_name(symbol: str) -> str | None:
    """
    Try to resolve a short ticker to a full company name via Yahoo Finance's unauthenticated search.
    Returns a name string or None if not found/failed.
    """
    if not looks_like_ticker(symbol):
        return None

    try:
        import requests  # type: ignore
    except ModuleNotFoundError:
        return None

    try:
        resp = requests.get(
            YAHOO_SEARCH_URL,
            params={"q": symbol, "quotesCount": 1, "newsCount": 0},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    sym_upper = symbol.upper()
    for quote in data.get("quotes", []):
        quote_sym = (quote.get("symbol") or "").upper()
        if quote_sym != sym_upper:
            continue
        name = quote.get("longname") or quote.get("shortname")
        if name:
            return str(name).strip()
    return None

