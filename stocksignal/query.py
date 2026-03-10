from __future__ import annotations

from typing import Sequence

from .keywords import normalize_for_query
from .symbols import looks_like_ticker


def build_query(symbol: str, keywords: Sequence[str] | None, english_only: bool = True) -> str:
    symbol = symbol.strip()
    if not symbol:
        raise ValueError("A stock symbol or company name is required.")

    tickerish = looks_like_ticker(symbol)
    if " " in symbol:
        symbol_clause = f'"{symbol}"'
    elif tickerish and len(symbol) < 5:
        # Avoid GDELT "phrase too short" errors for short tickers
        symbol_clause = symbol
    else:
        symbol_clause = f'("{symbol}" OR {symbol})'

    parts: list[str] = [symbol_clause]

    normalized = normalize_for_query(keywords)
    if normalized:
        if len(normalized) == 1:
            parts.append(normalized[0])
        else:
            parts.append("(" + " OR ".join(normalized) + ")")

    if english_only:
        parts.append("sourcelang:english")

    return " AND ".join(parts)
