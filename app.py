from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_searchbox import st_searchbox

from stocksignal.config import MAX_RECORDS, MIN_KEYWORD_LEN
from stocksignal.gdelt import fetch_articles
from stocksignal.keywords import normalize_keywords
from stocksignal.sentiment import aggregate_sentiment, score_articles
from stocksignal.symbols import expand_symbol_to_company_name
from stocksignal.ticker_list import filter_tickers, load_ticker_list_from_source


st.set_page_config(
    page_title="StockSignal",
    page_icon="📰",
    layout="wide",
)


def _format_seen_date(raw: str | None) -> str:
    """Convert GDELT seendate (e.g. 20260309T184500Z) to human-readable."""
    if not raw or not isinstance(raw, str):
        return raw or ""
    s = raw.strip()
    if len(s) < 8:
        return raw
    try:
        # YYYYMMDD or YYYYMMDDTHHMMSSZ
        y, m, d = int(s[:4]), int(s[4:6]), int(s[6:8])
        if "T" in s and len(s) >= 15:
            h, i, sec = int(s[9:11]), int(s[11:13]), int(s[13:15])
            dt = datetime(y, m, d, h, i, sec)
            return dt.strftime("%b %d, %Y %I:%M %p")
        dt = datetime(y, m, d)
        return dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return raw


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
  .block-container { padding-top: 1.5rem; padding-bottom: 2.5rem; max-width: 100%; }
  [data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 600; }
  [data-testid="stSidebar"] .block-container { padding-top: 1rem; }
  [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:last-child { padding-bottom: 0.5rem; }
  h1 { font-weight: 700; letter-spacing: -0.02em; }
  .stCaption { color: var(--text-muted, #94a3b8); }
  [data-testid="stSidebar"] .sidebar-brand { font-size: 2rem !important; font-weight: 700 !important; letter-spacing: -0.03em; padding: 0 0 1.75rem !important; margin: -0.25rem 0 1.25rem 0 !important; border-bottom: 3px solid rgba(255,255,255,0.2); width: 100%; line-height: 1.2; box-sizing: border-box; display: block; }
</style>
""",
    unsafe_allow_html=True,
)


st.title("StockSignal")
st.markdown("**Extract sentiment signals from recent financial news.**")
st.caption("Powered by GDELT global news data and VADER sentiment analysis.")
st.markdown("")  # spacing

# Example searches — only visible before first search; prefill sidebar when clicked
if not st.session_state.get("has_searched", False):
    EXAMPLE_SEARCHES = [
        ("NVDA", "AI chips"),
        ("AAPL", "iphone"),
        ("MSFT", "earnings"),
    ]
    st.markdown("**Try examples:**")
    ex_cols = st.columns(len(EXAMPLE_SEARCHES))
    for i, (sym, kw) in enumerate(EXAMPLE_SEARCHES):
        with ex_cols[i]:
            if st.button(f"{sym} – {kw}", key=f"ex_{sym}_{i}", width="stretch"):
                st.session_state["ticker_symbol"] = sym
                st.session_state["ticker_searchterm"] = sym
                st.session_state["keyword_input"] = kw
                # Clear searchbox internal state so it uses our default on rerun
                for k in list(st.session_state.keys()):
                    if k == "ticker_searchbox" or (isinstance(k, str) and k.startswith("ticker_searchbox")):
                        del st.session_state[k]
                st.rerun()


def _ticker_search(searchterm: str) -> list[tuple[str, str]]:
    """Return (display_label, value) for streamlit-searchbox; value = symbol for GDELT."""
    # Track the raw text the user is typing so we can restore it after reruns/clears
    cleaned = (searchterm or "").strip()
    st.session_state["ticker_searchterm"] = cleaned

    if len(cleaned) < 2:
        return []

    tickers = _ticker_list()
    matches = filter_tickers(tickers, cleaned, limit=50)
    return [(f"{name} ({sym})", sym) for sym, name in matches]


with st.sidebar:
    st.markdown('<div class="sidebar-brand">StockSignal</div>', unsafe_allow_html=True)
    st.subheader("Search")
    # Use session_state so the box doesn't reset while typing or after clearing
    last_searchterm = st.session_state.get("ticker_searchterm", "MSFT")
    last_symbol = st.session_state.get("ticker_symbol", last_searchterm)

    selected = st_searchbox(
        _ticker_search,
        key="ticker_searchbox",
        label="Ticker or company name",
        placeholder="e.g. AAPL, NVIDIA, Bank of America",
        default=last_symbol,
        default_searchterm=last_searchterm,
        default_use_searchterm=True,
        help="Type to search 5,000+ NASDAQ symbols; pick from dropdown or just press Enter to use what you typed.",
    )
    symbol = (selected or "").strip()
    # If the user cleared the box, also clear the stored symbol so we don't snap back to a ticker.
    if symbol:
        st.session_state["ticker_symbol"] = symbol
    else:
        st.session_state["ticker_symbol"] = ""
    keyword_text = st.text_input(
        "Keywords (comma separated)",
        value=st.session_state.get("keyword_input", "guidance, investigation"),
        key="keyword_input",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        days = st.number_input(
            "Days back",
            min_value=0,
            max_value=60,
            value=5,
            step=1,
            help="How many days of history to search in GDELT (0 = all available). Higher values can return more articles but may be less focused on recent news.",
        )
    with col_b:
        limit = st.number_input(
            "Limit",
            min_value=1,
            max_value=MAX_RECORDS,
            value=40,
            step=5,
            help=f"Maximum number of articles to fetch from GDELT (1–{MAX_RECORDS}). Lower = faster and fewer API calls; higher = broader coverage but slightly higher chance of rate limiting.",
        )

    english_only = st.toggle("English only", value=True)
    auto_expand = st.toggle("Auto-expand short tickers", value=True, help="If GDELT complains the phrase is too short, retry using the Yahoo Finance company name.")
    show_sentiment = st.toggle("Show sentiment (VADER)", value=True, help="Score each headline with VADER; show sentiment column and aggregate.")

    run = st.button("Search", type="primary", width="stretch")

    st.divider()
    st.caption(
        f"Ticker list: NASDAQ listings (refreshed daily).  \n"
        f"Keywords &lt;{MIN_KEYWORD_LEN} chars ignored (GDELT)."
    )
    st.markdown("---")
    st.caption("**StockSignal** · GDELT + VADER")


if not run:
    st.info("Set your filters in the sidebar, then click **Search**.")
    st.stop()

st.session_state["has_searched"] = True  # Hide "Try examples" after first search

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

# Order: date, title, then compact meta, then link — reduces horizontal scroll
preferred = ["seen_date", "title", "source", "domain", "lang"]
if show_sentiment and "sentiment" in df.columns:
    preferred.append("sentiment")
    if "sentiment_compound" in df.columns:
        preferred.append("sentiment_compound")
preferred.append("url")
df = df[[c for c in preferred if c in df.columns]]

if "seen_date" in df.columns:
    df["seen_date"] = df["seen_date"].map(_format_seen_date)
# Shorten domain for table fit (strip protocol, truncate with ellipsis)
if "domain" in df.columns:
    dom = df["domain"].astype(str).str.replace(r"^https?://", "", regex=True)
    df["domain"] = dom.where(dom.str.len() <= 26, dom.str[:24] + "…")

# Top metrics row
if show_sentiment:
    col1, col2, col3, col4 = st.columns(4)
    agg = aggregate_sentiment(articles)
    col1.metric("Articles", f"{len(articles)}")
    col2.metric("Days back", f"{int(days)}")
    col3.metric("Avg score", f"{agg['mean_compound']:+.2f}")
    col4.metric("Updated", datetime.now().strftime("%Y-%m-%d %H:%M"))
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("Articles", f"{len(articles)}")
    col2.metric("Days back", f"{int(days)}")
    col3.metric("Updated", datetime.now().strftime("%Y-%m-%d %H:%M"))

# Sentiment Summary card (when sentiment is on)
if show_sentiment and "sentiment" in (articles[0] or {}):
    agg = aggregate_sentiment(articles)
    with st.container(border=True):
        st.markdown("**Sentiment Summary**")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Positive", str(agg["positive"]))
        s2.metric("Neutral", str(agg["neutral"]))
        s3.metric("Negative", str(agg["negative"]))
        s4.metric("Average score", f"{agg['mean_compound']:+.2f}")

# Article cards: [badge] Title — Source | Date — Open article →
st.markdown("---")
st.subheader("Articles")
for i, art in enumerate(articles):
    title = (art.get("title") or "No title").strip()
    url = (art.get("url") or "").strip()
    source = (art.get("source") or "—").strip()
    raw_date = art.get("seendate")
    date_str = _format_seen_date(raw_date) if raw_date else "—"
    sentiment = (art.get("sentiment") or "").strip()
    with st.container(border=True):
        if sentiment:
            badge = "🟢" if sentiment == "Positive" else "🟡" if sentiment == "Neutral" else "🔴"
            st.markdown(f"{badge} **{sentiment}**")
        st.markdown(f"**{title}**")
        st.caption(f"{source} · {date_str}")
        if url:
            st.link_button("Open article →", url=url, type="secondary")

st.markdown("---")
with st.expander("View as table"):
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            "seen_date": st.column_config.TextColumn("Date", width="small"),
            "title": st.column_config.TextColumn("Title", width="medium"),
            "source": st.column_config.TextColumn("Source", width="small"),
            "domain": st.column_config.TextColumn("Domain", width="small"),
            "lang": st.column_config.TextColumn("Lang", width="small"),
            "url": st.column_config.LinkColumn("Link", width="small"),
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

