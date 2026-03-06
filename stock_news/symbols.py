from __future__ import annotations

from .config import YAHOO_SEARCH_URL


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

