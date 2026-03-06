from __future__ import annotations

from datetime import datetime, timedelta, timezone
import random
import time
from typing import Any, Sequence

from .config import GDELT_URL, MAX_RECORDS
from .query import build_query


def _parse_retry_after_seconds(value: str | None) -> int | None:
    if not value:
        return None
    try:
        seconds = int(value.strip())
    except ValueError:
        return None
    if seconds < 0:
        return None
    return seconds


def fetch_articles(
    symbol: str,
    keywords: Sequence[str] | None,
    days: int = 3,
    limit: int = 25,
    english_only: bool = True,
) -> list[dict[str, str | None]]:
    limit = max(1, min(limit, MAX_RECORDS))
    days = max(0, days)

    query = build_query(symbol, keywords, english_only)

    try:
        import requests  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            'Missing dependency "requests". Install with: pip install -r requirements.txt'
        ) from exc

    params: dict[str, Any] = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": limit,
        "sort": "datedesc",
    }

    if days > 0:
        start = datetime.now(timezone.utc) - timedelta(days=days)
        params["startdatetime"] = start.strftime("%Y%m%d%H%M%S")

    headers = {
        "User-Agent": "stock-news (streamlit; educational) - rate-limit friendly",
        "Accept": "application/json,text/plain,*/*",
    }

    last_error: Exception | None = None
    # GDELT may rate-limit. Retry a few times with backoff, respecting Retry-After if present.
    for attempt in range(4):
        try:
            response = requests.get(GDELT_URL, params=params, headers=headers, timeout=10)
            if response.status_code == 429:
                retry_after = _parse_retry_after_seconds(response.headers.get("Retry-After"))
                base = retry_after if retry_after is not None else (2**attempt)
                # add a touch of jitter so multiple clients don't sync up
                sleep_s = min(30, base) + random.uniform(0.0, 0.75)
                time.sleep(sleep_s)
                continue

            response.raise_for_status()
            break
        except requests.exceptions.HTTPError as exc:
            last_error = exc
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (429, 500, 502, 503, 504) and attempt < 3:
                sleep_s = min(30, (2**attempt)) + random.uniform(0.0, 0.75)
                time.sleep(sleep_s)
                continue
            raise
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt < 3:
                sleep_s = min(30, (2**attempt)) + random.uniform(0.0, 0.75)
                time.sleep(sleep_s)
                continue
            raise RuntimeError(f"Network error while contacting GDELT: {exc}") from exc
    else:
        # shouldn't happen because we break on success, but keep a defensive fallback
        raise RuntimeError(f"GDELT request failed after retries: {last_error}")

    if response.status_code == 429:
        raise RuntimeError(
            "GDELT rate-limited this request (HTTP 429). Please wait 30–60 seconds and try again, "
            "or reduce your search frequency/limit."
        )

    raw_text = response.text
    try:
        data = response.json()
    except ValueError as exc:
        snippet = (raw_text or "").strip()
        lower = snippet.lower()
        if "phrase is too short" in lower:
            hint = (
                "GDELT rejected the query because a phrase is too short. "
                'Try a longer company name (e.g., "Meta Platforms"), add more keywords and ensure you are using the correct stock symbol/name.'
            )
        elif snippet:
            hint = f"GDELT returned non-JSON: {snippet[:300]}"
        else:
            hint = "GDELT returned an empty or non-JSON response."
        raise RuntimeError(hint) from exc

    if isinstance(data, dict):
        msg = data.get("error") or data.get("message")
        if msg:
            raise RuntimeError(f"GDELT returned an error: {msg}")

    articles = (data or {}).get("articles", [])
    results: list[dict[str, str | None]] = []
    for article in articles:
        results.append(
            {
                "title": article.get("title"),
                "url": article.get("url"),
                "seendate": article.get("seendate"),
                "source": article.get("sourceCommonName") or article.get("sourcecountry"),
                "language": article.get("language"),
                "domain": article.get("domain"),
            }
        )
    return results

