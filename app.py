from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from stock_news.config import MAX_RECORDS, MIN_KEYWORD_LEN
from stock_news.gdelt import fetch_articles
from stock_news.keywords import normalize_keywords
from stock_news.symbols import expand_symbol_to_company_name


st.set_page_config(
    page_title="Stock News",
    page_icon="📰",
    layout="wide",
)


def _parse_keywords(text: str) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    # Allow comma-separated entry in one box
    return [x.strip() for x in text.split(",") if x.strip()]


@st.cache_data(ttl=600, show_spinner=False)
def _cached_fetch(
    symbol: str,
    keywords: tuple[str, ...],
    days: int,
    limit: int,
    english_only: bool,
) -> list[dict[str, str | None]]:
    return fetch_articles(
        symbol=symbol,
        keywords=list(keywords),
        days=days,
        limit=limit,
        english_only=english_only,
    )


st.markdown(
    """
<style>
  .block-container { padding-top: 1.25rem; padding-bottom: 2rem; }
  [data-testid="stMetricValue"] { font-size: 1.55rem; }
  [data-testid="stSidebar"] .block-container { padding-top: 1rem; }
</style>
""",
    unsafe_allow_html=True,
)


st.title("Stock News")
st.caption("Search recent coverage via the GDELT 2.1 Doc API. English-only by default.")


with st.sidebar:
    st.subheader("Search")
    symbol = st.text_input("Ticker or company", value="MSFT", help='Examples: "MSFT", "NVIDIA", "Bank of America"')
    keyword_text = st.text_input("Keywords (comma separated)", value="guidance, investigation")

    col_a, col_b = st.columns(2)
    with col_a:
        days = st.number_input("Days back", min_value=0, max_value=60, value=5, step=1)
    with col_b:
        limit = st.number_input("Limit", min_value=1, max_value=MAX_RECORDS, value=40, step=5)

    english_only = st.toggle("English only", value=True)
    auto_expand = st.toggle("Auto-expand short tickers", value=True, help="If GDELT complains the phrase is too short, retry using the Yahoo Finance company name.")

    run = st.button("Search", type="primary", use_container_width=True)

    st.divider()
    st.caption(f"Keywords shorter than {MIN_KEYWORD_LEN} characters are ignored (GDELT restriction).")


if not run:
    st.info("Set your filters in the sidebar, then click **Search**.")
    st.stop()

raw_keywords = _parse_keywords(keyword_text)
keywords, skipped = normalize_keywords(raw_keywords)
if skipped:
    st.warning(f"Skipped short keywords: {', '.join(skipped)}")

if not symbol.strip():
    st.error("Please enter a ticker or company name.")
    st.stop()

with st.spinner("Fetching articles..."):
    try:
        articles = _cached_fetch(
            symbol=symbol.strip(),
            keywords=tuple(keywords),
            days=int(days),
            limit=int(limit),
            english_only=bool(english_only),
        )
    except RuntimeError as exc:
        msg = str(exc)
        lowered = msg.lower()
        if auto_expand and "phrase is too short" in lowered:
            expanded = expand_symbol_to_company_name(symbol.strip())
            if expanded and expanded.lower() != symbol.strip().lower():
                st.warning(f'Query phrase too short for "{symbol}". Retrying with "{expanded}".')
                articles = _cached_fetch(
                    symbol=expanded,
                    keywords=tuple(keywords),
                    days=int(days),
                    limit=int(limit),
                    english_only=bool(english_only),
                )
            else:
                st.error(msg)
                st.stop()
        else:
            st.error(msg)
            st.stop()

st.subheader("Results")

col1, col2, col3 = st.columns(3)
col1.metric("Articles", f"{len(articles)}")
col2.metric("Days back", f"{int(days)}")
col3.metric("Updated", datetime.now().strftime("%Y-%m-%d %H:%M"))

if not articles:
    st.warning("No articles found. Try increasing **Days back**, widening keywords, or using the full company name.")
    st.stop()

df = pd.DataFrame(articles)
df = df.rename(
    columns={
        "seendate": "seen_date",
        "source": "source",
        "domain": "domain",
        "language": "lang",
        "title": "title",
        "url": "url",
    }
)

preferred = ["seen_date", "source", "domain", "lang", "title", "url"]
df = df[[c for c in preferred if c in df.columns]]

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "url": st.column_config.LinkColumn("Link"),
        "title": st.column_config.TextColumn("Title", width="large"),
        "seen_date": st.column_config.TextColumn("Seen date"),
        "source": st.column_config.TextColumn("Source"),
        "domain": st.column_config.TextColumn("Domain"),
        "lang": st.column_config.TextColumn("Lang", width="small"),
    },
)

