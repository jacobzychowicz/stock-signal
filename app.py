from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_searchbox import st_searchbox

from stock_news.config import MAX_RECORDS, MIN_KEYWORD_LEN
from stock_news.gdelt import fetch_articles
from stock_news.keywords import normalize_keywords
from stock_news.sentiment import aggregate_sentiment, score_articles
from stock_news.symbols import expand_symbol_to_company_name
from stock_news.ticker_list import filter_tickers, load_ticker_list_from_source


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


@st.cache_data(ttl=86400, show_spinner=False)
def _ticker_list() -> list[tuple[str, str]]:
    """Load full ticker list from CSV (NASDAQ listings); fallback to built-in list on failure."""
    return load_ticker_list_from_source()


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


def _ticker_search(searchterm: str) -> list[tuple[str, str]]:
    """Return (display_label, value) for streamlit-searchbox; value = symbol for GDELT."""
    if not searchterm or len(searchterm.strip()) < 2:
        return []
    tickers = _ticker_list()
    matches = filter_tickers(tickers, searchterm.strip(), limit=50)
    return [(f"{name} ({sym})", sym) for sym, name in matches]


with st.sidebar:
    st.subheader("Search")
    symbol = st_searchbox(
        _ticker_search,
        key="ticker_searchbox",
        label="Ticker or company name",
        placeholder="e.g. AAPL, NVIDIA, Bank of America",
        default="MSFT",
        default_searchterm="MSFT",
        default_use_searchterm=True,
        help="Type to search 5,000+ NASDAQ symbols; pick from dropdown or use your text.",
    )
    symbol = (symbol or "").strip()
    keyword_text = st.text_input("Keywords (comma separated)", value="guidance, investigation")

    col_a, col_b = st.columns(2)
    with col_a:
        days = st.number_input("Days back", min_value=0, max_value=60, value=5, step=1)
    with col_b:
        limit = st.number_input("Limit", min_value=1, max_value=MAX_RECORDS, value=40, step=5)

    english_only = st.toggle("English only", value=True)
    auto_expand = st.toggle("Auto-expand short tickers", value=True, help="If GDELT complains the phrase is too short, retry using the Yahoo Finance company name.")
    show_sentiment = st.toggle("Show sentiment (VADER)", value=True, help="Score each headline with VADER; show sentiment column and aggregate.")

    run = st.button("Search", type="primary", use_container_width=True)

    st.divider()
    st.caption(f"Ticker list: NASDAQ listings (refreshed daily). Keywords &lt;{MIN_KEYWORD_LEN} chars ignored (GDELT).")


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

if show_sentiment:
    try:
        score_articles(articles, title_key="title")
    except RuntimeError as e:
        st.warning(f"Sentiment skipped: {e}")
        show_sentiment = False

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
if show_sentiment and "sentiment" in df.columns:
    preferred.append("sentiment")
    if "sentiment_compound" in df.columns:
        preferred.append("sentiment_compound")
df = df[[c for c in preferred if c in df.columns]]

if show_sentiment:
    agg = aggregate_sentiment(articles)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Articles", f"{len(articles)}")
    col2.metric("Days back", f"{int(days)}")
    col3.metric("Avg sentiment", f"{agg['mean_compound']:.2f}")
    col4.metric("Updated", datetime.now().strftime("%Y-%m-%d %H:%M"))
    st.caption(f"Sentiment: {agg['positive']} positive, {agg['neutral']} neutral, {agg['negative']} negative (VADER on headlines)")
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("Articles", f"{len(articles)}")
    col2.metric("Days back", f"{int(days)}")
    col3.metric("Updated", datetime.now().strftime("%Y-%m-%d %H:%M"))

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
        **(
            {
                "sentiment": st.column_config.TextColumn("Sentiment", width="small"),
                "sentiment_compound": st.column_config.NumberColumn("Compound", format="%.2f", width="small"),
            }
            if show_sentiment and "sentiment" in df.columns
            else {}
        ),
    },
)

